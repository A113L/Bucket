# --- OpenCL Kernel Source (Implemented Hashcat Rules) ---
kernel_source = f"""
// Helper function to convert char digit/letter to int position
unsigned int char_to_pos(unsigned char c) {{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'Z') return c - 'A' + 10;
    // Return a value guaranteed to fail bounds checks
    return 0xFFFFFFFF; 
}}

__kernel void bfs_kernel(
    __global const unsigned char* base_words_in,
    __global const unsigned short* rules_in,
    __global unsigned char* result_buffer,
    const unsigned int num_words,
    const unsigned int num_rules,
    const unsigned int max_word_len,
    const unsigned int max_rule_len_padded,
    const unsigned int max_output_len_padded)
{{
    unsigned int global_id = get_global_id(0);
    unsigned int word_idx = global_id / num_rules;
    unsigned int rule_idx = global_id % num_rules;

    if (word_idx >= num_words) return;

    __global const unsigned char* current_word_ptr = base_words_in + word_idx * max_word_len;
    __global const unsigned short* rule_id_ptr = rules_in + rule_idx * (max_rule_len_padded + 1); 
    __global const unsigned char* rule_ptr = (__global const unsigned char*)rules_in + rule_idx * (max_rule_len_padded + 1) * sizeof(unsigned short) + sizeof(unsigned short);

    unsigned int rule_id = rule_id_ptr[0];

    __global unsigned char* result_ptr = result_buffer + global_id * max_output_len_padded;

    unsigned int word_len = 0;
    for (unsigned int i = 0; i < max_word_len; i++) {{
        if (current_word_ptr[i] == 0) {{
            word_len = i;
            break;
        }}
    }}
    
    unsigned int out_len = 0;
    bool changed_flag = false;
    
    // Zero out the result buffer for this thread
    for(unsigned int i = 0; i < max_output_len_padded; i++) {{
        result_ptr[i] = 0;
    }}

    // --- Unify rule ID blocks (Substituted from Python) ---
    unsigned int start_id_simple = {start_id_simple};
    unsigned int end_id_simple = start_id_simple + {num_simple_rules};
    unsigned int start_id_TD = {start_id_TD};
    unsigned int end_id_TD = start_id_TD + {num_td_rules};
    unsigned int start_id_s = {start_id_s};
    unsigned int end_id_s = start_id_s + {num_s_rules};
    unsigned int start_id_A = {start_id_A};
    unsigned int end_id_A = start_id_A + {num_a_rules};
    
    // --- NEW rule ID range (Group B) ---
    // Assuming these new rules follow sequentially after Group A
    unsigned int start_id_new = end_id_A; 
    unsigned int end_id_new = start_id_new + 13; // Count of new rules: p, {, }, [, ], x, O, i, o, ', z, Z, q
    
    // --- Kernel Logic (Rule Transformation) ---
    
    if (rule_id >= start_id_simple && rule_id < end_id_simple) {{ // Simple rules (l, u, c, C, t, r, k, :, d, f)
        switch(rule_id - start_id_simple) {{
            case 0: {{ // 'l' (lowercase)
                out_len = word_len;
                for (unsigned int i = 0; i < word_len; i++) {{
                    unsigned char c = current_word_ptr[i];
                    if (c >= 'A' && c <= 'Z') {{
                        result_ptr[i] = c + 32;
                        changed_flag = true;
                    }} else {{
                        result_ptr[i] = c;
                    }}
                }}
                break;
            }}
            case 1: {{ // 'u' (uppercase)
                out_len = word_len;
                for (unsigned int i = 0; i < word_len; i++) {{
                    unsigned char c = current_word_ptr[i];
                    if (c >= 'a' && c <= 'z') {{
                        result_ptr[i] = c - 32;
                        changed_flag = true;
                    }} else {{
                        result_ptr[i] = c;
                    }}
                }}
                break;
            }}
            case 2: {{ // 'c' (capitalize)
                out_len = word_len;
                if (word_len > 0) {{
                    if (current_word_ptr[0] >= 'a' && current_word_ptr[0] <= 'z') {{
                        result_ptr[0] = current_word_ptr[0] - 32;
                        changed_flag = true;
                    }} else {{
                        result_ptr[0] = current_word_ptr[0];
                    }}
                    for (unsigned int i = 1; i < word_len; i++) {{
                        unsigned char c = current_word_ptr[i];
                        if (c >= 'A' && c <= 'Z') {{ // Ensure rest is lowercase
                            result_ptr[i] = c + 32;
                            changed_flag = true;
                        }} else {{
                            result_ptr[i] = c;
                        }}
                    }}
                }}
                break;
            }}
            case 3: {{ // 'C' (invert capitalize)
                out_len = word_len;
                if (word_len > 0) {{
                    if (current_word_ptr[0] >= 'A' && current_word_ptr[0] <= 'Z') {{
                        result_ptr[0] = current_word_ptr[0] + 32;
                        changed_flag = true;
                    }} else {{
                        result_ptr[0] = current_word_ptr[0];
                    }}
                    for (unsigned int i = 1; i < word_len; i++) {{
                        unsigned char c = current_word_ptr[i];
                        if (c >= 'a' && c <= 'z') {{ // Ensure rest is UPPERCASE
                            result_ptr[i] = c - 32;
                            changed_flag = true;
                        }} else {{
                            result_ptr[i] = c;
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
                        result_ptr[i] = c - 32;
                        changed_flag = true;
                    }} else if (c >= 'A' && c <= 'Z') {{
                        result_ptr[i] = c + 32;
                        changed_flag = true;
                    }} else {{
                        result_ptr[i] = c;
                    }}
                }}
                break;
            }}
            case 5: {{ // 'r' (reverse)
                out_len = word_len;
                if (word_len > 1) {{
                    for (unsigned int i = 0; i < word_len; i++) {{
                        result_ptr[i] = current_word_ptr[word_len - 1 - i];
                    }}
                    // Check if word actually changed
                    for (unsigned int i = 0; i < word_len; i++) {{
                        if (result_ptr[i] != current_word_ptr[i]) {{
                            changed_flag = true;
                            break;
                        }}
                    }}
                }} else {{
                    for (unsigned int i = 0; i < word_len; i++) {{
                        result_ptr[i] = current_word_ptr[i];
                    }}
                }}
                break;
            }}
            case 6: {{ // 'k' (swap first two chars)
                out_len = word_len;
                for(unsigned int i=0; i<word_len; i++) result_ptr[i] = current_word_ptr[i];
                if (word_len >= 2) {{
                    result_ptr[0] = current_word_ptr[1];
                    result_ptr[1] = current_word_ptr[0];
                    changed_flag = true;
                }}
                break;
            }}
            case 7: {{ // ':' (identity/no change)
                out_len = word_len;
                for(unsigned int i=0; i<word_len; i++) result_ptr[i] = current_word_ptr[i];
                changed_flag = false;
                break;
            }}
            case 8: {{ // 'd' (duplicate)
                out_len = word_len * 2;
                if (out_len >= max_output_len_padded) {{
                    out_len = 0;	
                    changed_flag = false;
                    break;
                }}
                for(unsigned int i=0; i<word_len; i++) {{
                    result_ptr[i] = current_word_ptr[i];
                    result_ptr[word_len+i] = current_word_ptr[i];
                }}
                changed_flag = true;
                break;
            }}
            case 9: {{ // 'f' (reflect: word + reverse(word))
                out_len = word_len * 2;
                if (out_len >= max_output_len_padded) {{
                    out_len = 0;
                    changed_flag = false;
                    break;
                }}
                for(unsigned int i=0; i<word_len; i++) {{
                    result_ptr[i] = current_word_ptr[i];
                    result_ptr[word_len+i] = current_word_ptr[word_len-1-i];
                }}
                changed_flag = true;
                break;
            }}
        }}
    }} else if (rule_id >= start_id_TD && rule_id < end_id_TD) {{ // T, D rules (Toggle at pos, Delete at pos)
        // Read position from the second byte of the rule (e.g., T1 -> byte '1')
        unsigned char operator_char = rule_ptr[0];
        unsigned char pos_char = rule_ptr[1];
        
        unsigned int pos_to_change = char_to_pos(pos_char);
        
        if (operator_char == 'T') {{ // 'T' (toggle case at pos)
            out_len = word_len;
            for (unsigned int i = 0; i < word_len; i++) {{
                result_ptr[i] = current_word_ptr[i];
            }}
            if (pos_to_change != 0xFFFFFFFF && pos_to_change < word_len) {{
                unsigned char c = current_word_ptr[pos_to_change];
                if (c >= 'a' && c <= 'z') {{
                    result_ptr[pos_to_change] = c - 32;
                    changed_flag = true;
                }} else if (c >= 'A' && c <= 'Z') {{
                    result_ptr[pos_to_change] = c + 32;
                    changed_flag = true;
                }}
            }}
        }}
        else if (operator_char == 'D') {{ // 'D' (delete char at pos)
            unsigned int out_idx = 0;
            if (pos_to_change != 0xFFFFFFFF && pos_to_change < word_len) {{
                for (unsigned int i = 0; i < word_len; i++) {{
                    if (i != pos_to_change) {{
                        result_ptr[out_idx++] = current_word_ptr[i];
                    }} else {{
                        changed_flag = true;
                    }}
                }}
            }} else {{
                for (unsigned int i = 0; i < word_len; i++) {{
                    result_ptr[i] = current_word_ptr[i];
                }}
                out_idx = word_len;
            }}
            out_len = out_idx;
        }}
    }}
    else if (rule_id >= start_id_s && rule_id < end_id_s) {{ // 's' rules (substitute char)
        out_len = word_len;
        for(unsigned int i=0; i<word_len; i++) result_ptr[i] = current_word_ptr[i];
        
        unsigned char find = rule_ptr[0];
        unsigned char replace = rule_ptr[1];
        for(unsigned int i = 0; i < word_len; i++) {{
            if (current_word_ptr[i] == find) {{
                result_ptr[i] = replace;
                changed_flag = true;
            }}
        }}
    }} else if (rule_id >= start_id_A && rule_id < end_id_A) {{ // Group A rules (Prepend ^, Append $, Delete all @)
        out_len = word_len;
        for(unsigned int i=0; i<word_len; i++) result_ptr[i] = current_word_ptr[i];
        
        unsigned char cmd = rule_ptr[0];
        unsigned char arg = rule_ptr[1];
        
        if (cmd == '^') {{ // Prepend
            if (word_len + 1 >= max_output_len_padded) {{
                out_len = 0;
                changed_flag = false;
            }} else {{
                // Shift all characters right
                for(unsigned int i=word_len; i>0; i--) {{
                    result_ptr[i] = result_ptr[i-1];
                }}
                result_ptr[0] = arg;
                out_len++;
                changed_flag = true;
            }}
        }} else if (cmd == '$') {{ // Append
            if (word_len + 1 >= max_output_len_padded) {{
                out_len = 0;
                changed_flag = false;
            }} else {{
                result_ptr[out_len] = arg;
                out_len++;
                changed_flag = true;
            }}
        }} else if (cmd == '@') {{ // Delete all instances of char
            unsigned int temp_idx = 0;
            for(unsigned int i=0; i<word_len; i++) {{
                if (result_ptr[i] != arg) {{
                    result_ptr[temp_idx++] = result_ptr[i];
                }} else {{
                    changed_flag = true;
                }}
            }}
            out_len = temp_idx;
        }}
    }}
    // --- START NEW GROUP B RULES ---
    else if (rule_id >= start_id_new && rule_id < end_id_new) {{ 
        
        // Default to copying the word for modification
        for(unsigned int i=0; i<word_len; i++) result_ptr[i] = current_word_ptr[i];
        out_len = word_len;

        unsigned char cmd = rule_ptr[0];
        unsigned int N = (len(rule_ptr) > 1) ? char_to_pos(rule_ptr[1]) : 0xFFFFFFFF;
        unsigned int M = (len(rule_ptr) > 2) ? char_to_pos(rule_ptr[2]) : 0xFFFFFFFF;
        unsigned char X = (len(rule_ptr) > 2) ? rule_ptr[2] : 0; // for i/o rules

        if (cmd == 'p') {{ // 'p' (Duplicate N times)
            if (N != 0xFFFFFFFF) {{
                unsigned int num_dupes = N;
                unsigned int total_len = word_len * (num_dupes + 1); 

                if (total_len >= max_output_len_padded || num_dupes == 0) {{
                    out_len = 0; 
                }} else {{
                    for (unsigned int j = 1; j <= num_dupes; j++) {{
                        unsigned int offset = word_len * j;
                        for (unsigned int i = 0; i < word_len; i++) {{
                            result_ptr[offset + i] = current_word_ptr[i];
                        }}
                    }}
                    out_len = total_len;
                    changed_flag = true;
                }}
            }}
        }} 
        
        else if (cmd == 'q') {{ // 'q' (Duplicate all characters)
            unsigned int total_len = word_len * 2;
            if (total_len >= max_output_len_padded) {{
                out_len = 0;
            }} else {{
                for (unsigned int i = 0; i < word_len; i++) {{
                    result_ptr[i * 2] = current_word_ptr[i];
                    result_ptr[i * 2 + 1] = current_word_ptr[i];
                }}
                out_len = total_len;
                changed_flag = true;
            }}
        }}

        else if (cmd == '{') {{ // '{' (Rotate Left)
            if (word_len > 0) {{
                unsigned char first_char = current_word_ptr[0];
                for (unsigned int i = 0; i < word_len - 1; i++) {{
                    result_ptr[i] = current_word_ptr[i + 1];
                }}
                result_ptr[word_len - 1] = first_char;
                changed_flag = true;
            }}
        }} 
        
        else if (cmd == '}') {{ // '}' (Rotate Right)
            if (word_len > 0) {{
                unsigned char last_char = current_word_ptr[word_len - 1];
                for (unsigned int i = word_len - 1; i > 0; i--) {{
                    result_ptr[i] = current_word_ptr[i - 1];
                }}
                result_ptr[0] = last_char;
                changed_flag = true;
            }}
        }}
        
        else if (cmd == '[') {{ // '[' (Truncate Left / Delete first char)
            if (word_len > 0) {{
                for (unsigned int i = 0; i < word_len - 1; i++) {{
                    result_ptr[i] = current_word_ptr[i + 1];
                }}
                out_len = word_len - 1;
                changed_flag = true;
            }}
        }} 
        
        else if (cmd == ']') {{ // ']' (Truncate Right / Delete last char)
            if (word_len > 0) {{
                // Word already copied up to word_len - 1
                out_len = word_len - 1;
                changed_flag = true;
            }}
        }} 
        
        else if (cmd == 'x') {{ // 'xNM' (Extract range, N=start, M=length)
            unsigned int start = N;
            unsigned int length = M;
            
            if (start != 0xFFFFFFFF && length != 0xFFFFFFFF && start < word_len && length > 0) {{
                unsigned int end = start + length;
                if (end > word_len) end = word_len;
                
                out_len = 0;
                for (unsigned int i = start; i < end; i++) {{
                    result_ptr[out_len++] = current_word_ptr[i];
                }}
                changed_flag = true;
            }} else {{
                // Invalid range results in an empty word
                out_len = 0; 
            }}
        }}
        
        else if (cmd == 'O') {{ // 'ONM' (Omit range, N=start, M=length)
            unsigned int start = N;
            unsigned int length = M;
            
            if (start != 0xFFFFFFFF && length != 0xFFFFFFFF && length > 0) {{
                unsigned int skip_start = (start < word_len) ? start : word_len;
                unsigned int skip_end = (skip_start + length < word_len) ? skip_start + length : word_len;
                
                out_len = 0;
                for (unsigned int i = 0; i < word_len; i++) {{
                    if (i < skip_start || i >= skip_end) {{
                        result_ptr[out_len++] = current_word_ptr[i];
                    }} else {{
                        changed_flag = true;
                    }}
                }}
            }}
        }}

        else if (cmd == 'i') {{ // 'iNX' (Insert char X at position N)
            unsigned int pos = N;
            unsigned char insert_char = X;

            if (pos != 0xFFFFFFFF && word_len + 1 < max_output_len_padded) {{
                unsigned int final_pos = (pos > word_len) ? word_len : pos;
                out_len = word_len + 1;

                // Copy and shift
                unsigned int current_idx = 0;
                for (unsigned int i = 0; i < out_len; i++) {{
                    if (i == final_pos) {{
                        result_ptr[i] = insert_char;
                    }} else {{
                        result_ptr[i] = current_word_ptr[current_idx++];
                    }}
                }}
                changed_flag = true;
            }} else {{
                out_len = 0;
            }}
        }}

        else if (cmd == 'o') {{ // 'oNX' (Overwrite char at position N with X)
            unsigned int pos = N;
            unsigned char new_char = X;

            if (pos != 0xFFFFFFFF && pos < word_len) {{
                result_ptr[pos] = new_char;
                changed_flag = true;
            }}
        }}
        
        else if (cmd == '\'') {{ // "'N" (Truncate at position N)
            unsigned int pos = N;
            
            if (pos != 0xFFFFFFFF && pos < word_len) {{
                out_len = pos;
                changed_flag = true;
            }} 
        }}

        else if (cmd == 'z') {{ // 'zN' (Duplicate first char N times)
            unsigned int num_dupes = N;
            if (num_dupes != 0xFFFFFFFF && num_dupes > 0) {{
                unsigned int total_len = word_len + num_dupes;
                if (total_len < max_output_len_padded) {{
                    unsigned char first_char = current_word_ptr[0];
                    unsigned int out_idx = 0;
                    
                    // 1. Write duplicates
                    for (unsigned int i = 0; i < num_dupes; i++) {{
                        result_ptr[out_idx++] = first_char;
                    }}
                    // 2. Append original word
                    for (unsigned int i = 0; i < word_len; i++) {{
                        result_ptr[out_idx++] = current_word_ptr[i];
                    }}
                    out_len = total_len;
                    changed_flag = true;
                }} else {{
                    out_len = 0;
                }}
            }}
        }}

        else if (cmd == 'Z') {{ // 'ZN' (Duplicate last char N times)
            unsigned int num_dupes = N;
            if (num_dupes != 0xFFFFFFFF && num_dupes > 0) {{
                unsigned int total_len = word_len + num_dupes;
                if (total_len < max_output_len_padded) {{
                    unsigned char last_char = current_word_ptr[word_len - 1];
                    
                    // Copy original word first (it was already copied at the start of this block)
                    unsigned int out_idx = word_len;
                    
                    // Append duplicates
                    for (unsigned int i = 0; i < num_dupes; i++) {{
                        result_ptr[out_idx++] = last_char;
                    }}
                    out_len = total_len;
                    changed_flag = true;
                }} else {{
                    out_len = 0;
                }}
            }}
        }}

    }}
    // --- END NEW GROUP B RULES ---
    
    // Final output processing
    if (changed_flag && out_len > 0) {{
        if (out_len < max_output_len_padded) {{
                   result_ptr[out_len] = 0; // Null terminator
        }}
    }} else {{
        // If the word was not changed or rule execution failed/resulted in length 0, zero out the output
        for (unsigned int i = 0; i < max_output_len_padded; i++) {{
            result_ptr[i] = 0;
        }}
    }}
}}
"""
# --- End OpenCL Kernel Source ---
