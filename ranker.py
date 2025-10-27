import pyopencl as cl
import numpy as np
import collections
import argparse
import csv
from tqdm import tqdm
import math
import warnings
import os 

# --- WARNING FILTERS ---
warnings.filterwarnings("ignore", message="overflow encountered in scalar multiply")
try:
    warnings.filterwarnings("ignore", category=cl.CompilerWarning)
except AttributeError:
    # Handle case where pyopencl.CompilerWarning is not available
    pass
# -----------------------

# ====================================================================
# --- CONSTANTS CONFIGURATION (OPTIMIZED FOR RTX 3060 Ti 8GB) ---
# ====================================================================
MAX_WORD_LEN = 32
MAX_OUTPUT_LEN = MAX_WORD_LEN * 2
MAX_RULE_ARGS = 2
MAX_RULES_IN_BATCH = 128  
LOCAL_WORK_SIZE = 256     

# BATCH SIZE FOR WORDS: Processed per OpenCL kernel launch.
WORDS_PER_GPU_BATCH = 500000 

# Global Uniqueness Map Parameters (Hash Bitfield)
# 35 bits -> ~4 GB VRAM usage for the map
GLOBAL_HASH_MAP_BITS = 35
GLOBAL_HASH_MAP_WORDS = 1 << (GLOBAL_HASH_MAP_BITS - 5)
GLOBAL_HASH_MAP_BYTES = GLOBAL_HASH_MAP_WORDS * np.uint64(4) 
GLOBAL_HASH_MAP_MASK = (1 << (GLOBAL_HASH_MAP_BITS - 5)) - 1 

# Rule IDs 
START_ID_SIMPLE = 0
NUM_SIMPLE_RULES = 10
START_ID_TD = 10
NUM_TD_RULES = 20
START_ID_S = 30
NUM_S_RULES = 256 * 256 
START_ID_A = 30 + NUM_S_RULES 
NUM_A_RULES = 3 * 256
# ====================================================================

# --- KERNEL SOURCE (OpenCL C) ---
KERNEL_SOURCE = f"""
// FNV-1a Hash implementation in OpenCL
unsigned int fnv1a_hash_32(const unsigned char* data, unsigned int len) {{
    unsigned int hash = 2166136261U; 
    for (unsigned int i = 0; i < len; i++) {{
        hash ^= data[i];
        hash *= 16777619U; 
    }}
    return hash;
}}


__kernel void bfs_kernel(
    __global const unsigned char* base_words_in,
    __global const unsigned int* rules_in,         
    __global unsigned int* rule_uniqueness_counts, 
    __global unsigned int* global_hash_map,      
    const unsigned int num_words,
    const unsigned int num_rules_in_batch,
    const unsigned int max_word_len,
    const unsigned int max_output_len)
{{
    unsigned int global_id = get_global_id(0);
    
    // Calculate base indices and exit if ID is redundant
    unsigned int word_per_rule_count = num_words * num_rules_in_batch;
    if (global_id >= word_per_rule_count) return;

    unsigned int word_idx = global_id / num_rules_in_batch; 
    unsigned int rule_batch_idx = global_id % num_rules_in_batch; 

    // --- Local Variable Setup (Constants from Python) ---
    unsigned int start_id_simple = {START_ID_SIMPLE};
    unsigned int end_id_simple = start_id_simple + {NUM_SIMPLE_RULES};
    unsigned int start_id_TD = {START_ID_TD}; 
    unsigned int end_id_TD = start_id_TD + {NUM_TD_RULES};
    unsigned int start_id_s = {START_ID_S};
    unsigned int end_id_s = start_id_s + {NUM_S_RULES};
    unsigned int start_id_A = {START_ID_A};
    unsigned int end_id_A = start_id_A + {NUM_A_RULES};

    // Private memory buffer for the transformed word
    unsigned char result_temp[2 * {MAX_WORD_LEN}]; 
    
    __global const unsigned char* current_word_ptr = base_words_in + word_idx * max_word_len;
    
    unsigned int rule_size_in_int = 2 + {MAX_RULE_ARGS}; 
    __global const unsigned int* current_rule_ptr_int = rules_in + rule_batch_idx * rule_size_in_int; 
    
    unsigned int rule_id = current_rule_ptr_int[0]; 
    unsigned int rule_args_int = current_rule_ptr_int[1]; 
    
    // Find word length
    unsigned int word_len = 0;
    for (unsigned int i = 0; i < max_word_len; i++) {{
        if (current_word_ptr[i] == 0) {{
            word_len = i;
            break;
        }}
    }}
    
    if (word_len == 0 && rule_id < start_id_A ) {{
        return;
    }}
    
    unsigned int out_len = 0;
    bool changed_flag = false;
    
    // Zero out the temporary buffer
    for(unsigned int i = 0; i < max_output_len; i++) {{
        result_temp[i] = 0;
    }}

    // --- Kernel Logic (Rule Transformation) ---
    
    if (rule_id >= start_id_simple && rule_id < end_id_simple) {{ 
        
        switch(rule_id - start_id_simple) {{
            case 0: {{ // 'l' (lowercase)
                out_len = word_len;
                for (unsigned int i = 0; i < word_len; i++) {{
                    unsigned char c = current_word_ptr[i];
                    if (c >= 'A' && c <= 'Z') {{
                        result_temp[i] = c + 32;
                        changed_flag = true;
                    }} else {{
                        result_temp[i] = c;
                    }}
                }}
                break;
            }}
            case 1: {{ // 'u' (uppercase)
                out_len = word_len;
                for (unsigned int i = 0; i < word_len; i++) {{
                    unsigned char c = current_word_ptr[i];
                    if (c >= 'a' && c <= 'z') {{
                        result_temp[i] = c - 32;
                        changed_flag = true;
                    }} else {{
                        result_temp[i] = c;
                    }}
                }}
                break;
            }}
            case 2: {{ // 'c' (capitalize)
                out_len = word_len;
                if (word_len > 0) {{
                    if (current_word_ptr[0] >= 'a' && current_word_ptr[0] <= 'z') {{
                        result_temp[0] = current_word_ptr[0] - 32;
                        changed_flag = true;
                    }} else {{
                        result_temp[0] = current_word_ptr[0];
                    }}
                    for (unsigned int i = 1; i < word_len; i++) {{
                        unsigned char c = current_word_ptr[i];
                        if (c >= 'A' && c <= 'Z') {{ 
                            result_temp[i] = c + 32;
                            changed_flag = true;
                        }} else {{
                            result_temp[i] = c;
                        }}
                    }}
                }}
                break;
            }}
            case 3: {{ // 'C' (invert capitalize)
                out_len = word_len;
                if (word_len > 0) {{
                    if (current_word_ptr[0] >= 'A' && current_word_ptr[0] <= 'Z') {{
                        result_temp[0] = current_word_ptr[0] + 32;
                        changed_flag = true;
                    }} else {{
                        result_temp[0] = current_word_ptr[0];
                    }}
                    for (unsigned int i = 1; i < word_len; i++) {{
                        unsigned char c = current_word_ptr[i];
                        if (c >= 'a' && c <= 'z') {{ 
                            result_temp[i] = c - 32;
                            changed_flag = true;
                        }} else {{
                            result_temp[i] = c;
                        }}
                    }}
                }}
                break;
            }}
            case 4: {{ // 't' (toggle case)
                out_len = word_len;
                for (unsigned int i = 0; i < word_len; i++) {{
                    unsigned char c = current_word_ptr[i];
                    if (c >= 'a' && c <= 'z') {{
                        result_temp[i] = c - 32;
                        changed_flag = true;
                    }} else if (c >= 'A' && c <= 'Z') {{
                        result_temp[i] = c + 32;
                        changed_flag = true;
                    }} else {{
                        result_temp[i] = c;
                    }}
                }}
                break;
            }}
            case 5: {{ // 'r' (reverse)
                out_len = word_len;
                for (unsigned int i = 0; i < word_len; i++) {{
                    result_temp[i] = current_word_ptr[word_len - 1 - i];
                }}
                if (word_len > 1) {{
                    for (unsigned int i = 0; i < word_len; i++) {{
                        if (result_temp[i] != current_word_ptr[i]) {{
                            changed_flag = true;
                            break;
                        }}
                    }}
                }}
                break;
            }}
            case 6: {{ // 'k' (swap first two chars)
                out_len = word_len;
                for(unsigned int i=0; i<word_len; i++) result_temp[i] = current_word_ptr[i];
                if (word_len >= 2) {{
                    if (current_word_ptr[0] != current_word_ptr[1]) changed_flag = true;
                    result_temp[0] = current_word_ptr[1];
                    result_temp[1] = current_word_ptr[0];
                }}
                break;
            }}
            case 7: {{ // ':' (identity/no change)
                out_len = word_len;
                for(unsigned int i=0; i<word_len; i++) result_temp[i] = current_word_ptr[i];
                changed_flag = false;
                break;
            }}
            case 8: {{ // 'd' (duplicate)
                out_len = word_len * 2;
                if (out_len > max_output_len || out_len == 0) {{ 
                    out_len = 0;	
                    changed_flag = false;
                    break;
                }}
                for(unsigned int i=0; i<word_len; i++) {{
                    result_temp[i] = current_word_ptr[i];
                    result_temp[word_len+i] = current_word_ptr[i];
                }}
                changed_flag = true;
                break;
            }}
            case 9: {{ // 'f' (reflect: word + reverse(word))
                out_len = word_len * 2;
                if (out_len > max_output_len || out_len == 0) {{ 
                    out_len = 0;
                    changed_flag = false;
                    break;
                }}
                for(unsigned int i=0; i<word_len; i++) {{
                    result_temp[i] = current_word_ptr[i];
                    result_temp[word_len+i] = current_word_ptr[word_len-1-i];
                }}
                if (word_len > 0) changed_flag = true; 
                break;
            }}
        }}
    }} else if (rule_id >= start_id_TD && rule_id < end_id_TD) {{ // T, D rules
        
        unsigned char operator_char = rule_args_int & 0xFF; 
        unsigned int pos_char = (rule_args_int >> 8) & 0xFF; 
        
        unsigned int pos_to_change;
        if (pos_char >= '0' && pos_char <= '9') {{
            pos_to_change = pos_char - '0';
        }} else {{
            pos_to_change = max_word_len + 1; 
        }}

        
        if (operator_char == 'T') {{ // 'T' (toggle case at pos)
             out_len = word_len;
             for (unsigned int i = 0; i < word_len; i++) {{
                 result_temp[i] = current_word_ptr[i];
             }}
             if (pos_to_change < word_len) {{
                 unsigned char c = current_word_ptr[pos_to_change];
                 if (c >= 'a' && c <= 'z') {{
                     result_temp[pos_to_change] = c - 32;
                     changed_flag = true;
                 }} else if (c >= 'A' && c <= 'Z') {{
                     result_temp[pos_to_change] = c + 32;
                     changed_flag = true;
                 }}
             }}
        }} else if (operator_char == 'D') {{ // 'D' (delete char at pos)
            unsigned int out_idx = 0;
            if (pos_to_change < word_len) {{
                for (unsigned int i = 0; i < word_len; i++) {{
                    if (i != pos_to_change) {{
                        result_temp[out_idx++] = current_word_ptr[i];
                    }} else {{
                        changed_flag = true;
                    }}
                }}
            }} else {{
                for (unsigned int i = 0; i < word_len; i++) {{
                    result_temp[i] = current_word_ptr[i];
                }}
                out_idx = word_len;
                changed_flag = false;
            }}
            out_len = out_idx;
        }}
    }}
    else if (rule_id >= start_id_s && rule_id < end_id_s) {{ // 's' rules (substitute first)
        out_len = word_len;
        for(unsigned int i=0; i<word_len; i++) result_temp[i] = current_word_ptr[i];
        
        unsigned char find = rule_args_int & 0xFF; 
        unsigned char replace = (rule_args_int >> 8) & 0xFF; 
        
        for(unsigned int i = 0; i < word_len; i++) {{
            if (current_word_ptr[i] == find) {{
                result_temp[i] = replace;
                changed_flag = true;
            }}
        }}
    }} else if (rule_id >= start_id_A && rule_id < end_id_A) {{ // Group A rules
        
        unsigned char cmd = rule_args_int & 0xFF; 
        unsigned char arg = (rule_args_int >> 8) & 0xFF; 
        
        if (cmd != '@') {{
            for(unsigned int i=0; i<word_len; i++) result_temp[i] = current_word_ptr[i];
        }}
        
        if (cmd == '^') {{ // Prepend
            if (word_len + 1 > max_output_len) {{
                out_len = 0;
                changed_flag = false;
            }} else {{
                for(unsigned int i=word_len; i>0; i--) {{
                    result_temp[i] = current_word_ptr[i-1]; 
                }}
                result_temp[0] = arg;
                out_len = word_len + 1;
                changed_flag = true;
            }}
        }} else if (cmd == '$') {{ // Append
            if (word_len + 1 > max_output_len) {{
                out_len = 0;
                changed_flag = false;
            }} else {{
                out_len = word_len + 1;
                for(unsigned int i=0; i<word_len; i++) {{
                    result_temp[i] = current_word_ptr[i];
                }}
                result_temp[word_len] = arg;
                changed_flag = true;
            }}
        }} else if (cmd == '@') {{ // Delete all instances of char
            unsigned int temp_idx = 0;
            for(unsigned int i=0; i<word_len; i++) {{
                if (current_word_ptr[i] != arg) {{ 
                    result_temp[temp_idx++] = current_word_ptr[i];
                }} else {{
                    changed_flag = true;
                }}
            }}
            out_len = temp_idx;
        }}
    }}
    
    // --- Uniqueness Logic on GPU ---
    
    if (changed_flag) {{
        
        unsigned int word_hash = fnv1a_hash_32(result_temp, out_len);
        
        unsigned int map_index = (word_hash >> 5) & ({GLOBAL_HASH_MAP_MASK}); 
        unsigned int bit_index = word_hash & 31; 
        unsigned int check_bit = (1U << bit_index); 
        
        // Explicit cast to avoid 'address space mismatch' error
        __global unsigned int* map_ptr = (__global unsigned int*)&global_hash_map[map_index];

        // Atomically set the bit and check the old value
        unsigned int old_word = atomic_or(map_ptr, check_bit);
        
        // If the bit was NOT set before (i.e., this is a unique word)
        if (!(old_word & check_bit)) {{
            atomic_inc(&rule_uniqueness_counts[rule_batch_idx]);
        }}

    }} else {{
        return;
    }}
}}
"""

# --- HELPER FUNCTIONS (Python) ---

def fnv1a_hash_32_cpu(data):
    """Calculates FNV-1a hash for a byte array."""
    hash_val = np.uint32(2166136261)
    for byte in data:
        hash_val ^= np.uint32(byte)
        hash_val *= np.uint32(16777619) 
    return hash_val

def get_word_count(path):
    """Counts total words in file to set up progress bar."""
    print(f"Counting words in: {path}...")
    count = 0
    try:
        with open(path, 'r', encoding='latin-1', errors='ignore') as f:
            for line in f:
                count += 1
    except FileNotFoundError:
        print(f"Error: Wordlist file not found at: {path}")
        exit()

    print(f"Total words found: {count:,}")
    return count

def load_rules(path):
    """Loads Hashcat rules from file."""
    print(f"Loading rules from: {path}...")
    rules_list = []
    rule_id_counter = 0
    try:
        with open(path, 'r', encoding='latin-1') as f:
            for line in f:
                rule = line.strip()
                if not rule or rule.startswith('#'):
                    continue
                rules_list.append({'rule_data': rule, 'rule_id': rule_id_counter, 'score': 0})
                rule_id_counter += 1
    except FileNotFoundError:
        print(f"Error: Rules file not found at: {path}")
        exit()
        
    print(f"Loaded {len(rules_list)} rules.")
    return rules_list

def encode_rule(rule_str, rule_id, max_args):
    """Encodes a rule as an array of uint32: [rule ID, arguments]"""
    rule_size_in_int = 2 + max_args 
    encoded = np.zeros(rule_size_in_int, dtype=np.uint32) 
    encoded[0] = np.uint32(rule_id) 
    rule_chars = rule_str.encode('latin-1')
    args_int = 0
    if len(rule_chars) >= 1:
        args_int |= np.uint32(rule_chars[0]) 
    if len(rule_chars) >= 2:
        args_int |= (np.uint32(rule_chars[1]) << 8) 
    encoded[1] = args_int
    return encoded

def save_ranked_rules(ranking_list, output_path):
    """
    Saves ONLY the ranked rules (score > 0) to the output file,
    sorted from best to worst, and excludes ranking counters.
    """
    print(f"\nSaving ranked rules to: {output_path}...")
    
    ranked_rules = [rule for rule in ranking_list if rule.get('score', 0) > 0]

    if not ranked_rules:
        print("❌ No rules were ranked (score > 0). File not created.")
        return

    ranked_rules.sort(key=lambda rule: rule['score'], reverse=True)
                              
    try:
        with open(output_path, 'w', newline='\n', encoding='utf-8') as f:
            for rule in ranked_rules:
                f.write(f"{rule['rule_data']}\n")
        print(f"✅ Save completed successfully. File contains {len(ranked_rules)} rules sorted by uniqueness score.")
    except Exception as e:
        print(f"❌ Error while saving to file: {e}")

# --- WORDLIST ITERATOR ---

def wordlist_iterator(wordlist_path, max_len, batch_size):
    """
    Generator that yields batches of words and initial hashes directly from disk.
    """
    base_words_np = np.zeros((batch_size, max_len), dtype=np.uint8)
    base_hashes = []
    current_batch_count = 0
    
    with open(wordlist_path, 'r', encoding='latin-1', errors='ignore') as f:
        for line in f:
            word_str = line.strip()
            word = word_str.encode('latin-1')
            
            if 1 <= len(word) <= max_len:
                
                base_words_np[current_batch_count, :len(word)] = np.frombuffer(word, dtype=np.uint8)
                base_hashes.append(fnv1a_hash_32_cpu(word))
                
                current_batch_count += 1
                
                if current_batch_count == batch_size:
                    # Yield a copy of the filled part of the array to prevent issues 
                    # if the numpy array is modified before the next yield is consumed.
                    yield base_words_np.ravel().copy(), current_batch_count, base_hashes
                    
                    base_words_np.fill(0)
                    base_hashes = []
                    current_batch_count = 0
        
        if current_batch_count > 0:
            # Yield the final, potentially partial, batch
            words_to_yield = base_words_np[:current_batch_count * max_len].ravel().copy()
            yield words_to_yield, current_batch_count, base_hashes


# --- MAIN RANKING FUNCTION ---

def rank_rules_uniqueness(wordlist_path, rules_path, output_path):
    
    # 1. OpenCL Initialization
    try:
        platform = cl.get_platforms()[0]
        devices = platform.get_devices(cl.device_type.GPU)
        if not devices:
            devices = platform.get_devices(cl.device_type.ALL)
        device = devices[0]
        context = cl.Context([device])
        queue = cl.CommandQueue(context)
        
        rule_size_in_int = 2 + MAX_RULE_ARGS 

        # The error is fixed here: KERNEL_SOURCE is now a full string
        prg = cl.Program(context, KERNEL_SOURCE).build()
        kernel = prg.bfs_kernel 
        print(f"✅ OpenCL initialized on device: {device.name.strip()}")
    except Exception as e:
        print(f"❌ OpenCL initialization or kernel compilation error: {e}")
        try:
             print("\nBuild Log:")
             # Provide build log to the user in case of compilation failure
             print(prg.get_build_info(device, cl.program_build_info.LOG))
        except NameError:
             pass
        return

    # 2. Data Loading
    rules_list = load_rules(rules_path)
    total_words = get_word_count(wordlist_path)
    total_rules = len(rules_list)

    # 3. Hash Map Initialization (Still in VRAM)
    global_hash_map_np = np.zeros(GLOBAL_HASH_MAP_WORDS, dtype=np.uint32)
    print(f"📝 Global Hash Map initialized: {GLOBAL_HASH_MAP_BYTES / (1024*1024):.2f} MB allocated.")
    
    # 4. OpenCL Buffer Setup
    mf = cl.mem_flags

    # A) Base Word Input Buffer (Size limited by WORDS_PER_GPU_BATCH)
    base_words_size = WORDS_PER_GPU_BATCH * MAX_WORD_LEN * np.uint8().itemsize
    base_words_in_g = cl.Buffer(context, mf.READ_ONLY, base_words_size)
    
    # B) Rule Input Buffer (Filled once per rule batch)
    rules_np_batch = np.zeros(MAX_RULES_IN_BATCH * rule_size_in_int, dtype=np.uint32) 
    rules_in_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=rules_np_batch)
    
    # C) Hash Map (Transferred to VRAM once)
    global_hash_map_g = cl.Buffer(context, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=global_hash_map_np)
    
    # D) Rule Counter (Used in the GPU kernel)
    rule_uniqueness_counts_np = np.zeros(MAX_RULES_IN_BATCH, dtype=np.uint32)
    rule_uniqueness_counts_g = cl.Buffer(context, mf.READ_WRITE, rule_uniqueness_counts_np.nbytes)
    
    # 5. Rule Encoding (Done once)
    encoded_rules = [encode_rule(rule['rule_data'], rule['rule_id'], MAX_RULE_ARGS) for rule in rules_list]
    
    # 6. Disk-Based Ranking Loop
    
    word_iterator = wordlist_iterator(wordlist_path, MAX_WORD_LEN, WORDS_PER_GPU_BATCH)
    rule_batch_starts = list(range(0, total_rules, MAX_RULES_IN_BATCH))
    
    words_processed_total = 0
    
    word_batch_pbar = tqdm(total=total_words, desc="Processing wordlist from disk", unit=" word")

    # A. Iterate over word batches read from disk
    for base_words_np_batch, num_words_batch, base_hashes in word_iterator:
        
        # 6a. Initialize Hash Map for current word batch
        for h in base_hashes:
            map_index = (h >> 5) & GLOBAL_HASH_MAP_MASK
            bit_index = h & 31
            global_hash_map_np[map_index] |= (1 << bit_index)
        
        # Transfer the updated hash map to the GPU VRAM
        cl.enqueue_copy(queue, global_hash_map_g, global_hash_map_np).wait()
        
        # Update the GPU buffer with the current batch of words
        cl.enqueue_copy(queue, base_words_in_g, base_words_np_batch).wait()
        
        
        # B. Iterate over rule batches
        current_word_batch_scores = np.zeros(total_rules, dtype=np.uint32)
        
        for rule_batch_idx_start in rule_batch_starts:
            
            rule_batch_idx_end = min(rule_batch_idx_start + MAX_RULES_IN_BATCH, total_rules)
            current_batch_size = rule_batch_idx_end - rule_batch_idx_start
            
            # B1. Prepare and update rule buffer for the GPU
            rules_np_batch.fill(0) 
            rule_uniqueness_counts_np.fill(0) 
            
            for i in range(current_batch_size):
                encoded_rule = encoded_rules[rule_batch_idx_start + i]
                rules_np_batch[i * rule_size_in_int : (i + 1) * rule_size_in_int] = encoded_rule
                
            cl.enqueue_copy(queue, rules_in_g, rules_np_batch).wait() 
            cl.enqueue_copy(queue, rule_uniqueness_counts_g, rule_uniqueness_counts_np).wait() 

            # B2. Launch Kernel 
            desired_global_size = num_words_batch * current_batch_size
            global_size_actual = (int(math.ceil(desired_global_size / LOCAL_WORK_SIZE)) * LOCAL_WORK_SIZE,)
            local_size_actual = (LOCAL_WORK_SIZE,)
            
            event = kernel(queue, global_size_actual, local_size_actual, 
                           base_words_in_g,
                           rules_in_g,
                           rule_uniqueness_counts_g, 
                           global_hash_map_g,      
                           np.uint32(num_words_batch),
                           np.uint32(current_batch_size),
                           np.uint32(MAX_WORD_LEN),
                           np.uint32(MAX_OUTPUT_LEN))

            # B3. Fetch results and update scores for this word batch
            cl.enqueue_copy(queue, rule_uniqueness_counts_np, rule_uniqueness_counts_g, wait_for=[event]).wait()
            
            current_word_batch_scores[rule_batch_idx_start:rule_batch_idx_end] = rule_uniqueness_counts_np[:current_batch_size]

        # C. Update the main score list 
        newly_added_words_batch_total = 0
        for i in range(total_rules):
            rules_list[i]['score'] += int(current_word_batch_scores[i])
            newly_added_words_batch_total += int(current_word_batch_scores[i])

        words_processed_total += num_words_batch
        word_batch_pbar.update(num_words_batch)
        word_batch_pbar.set_postfix_str(f"New Hashes: +{newly_added_words_batch_total:,}")
        
    word_batch_pbar.close()

    # 7. Save Results (Only rules with score > 0)
    save_ranked_rules(rules_list, output_path)


# --- Script Execution ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="A tool for ranking Hashcat rules based on transformation uniqueness, utilizing OpenCL."
    )
    parser.add_argument(
        '-w', '--wordlist', 
        required=True, 
        help="Path to the base wordlist file."
    )
    parser.add_argument(
        '-r', '--rules', 
        required=True, 
        help="Path to the Hashcat rules file (.rule)."
    )
    parser.add_argument(
        '-o', '--output', 
        default='ranked_rules.rule', 
        help="Path to the output file (e.g., ranked_rules.rule)."
    )
    
    args = parser.parse_args()
    
    rank_rules_uniqueness(args.wordlist, args.rules, args.output)
