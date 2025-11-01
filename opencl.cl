// Helper function to convert char digit/letter to int position
unsigned int char_to_pos(unsigned char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'Z') return c - 'A' + 10;
    // Return a value guaranteed to fail bounds checks
    return 0xFFFFFFFF; 
}

// Helper function to get rule length
unsigned int rule_len(__global const unsigned char* rule_ptr, unsigned int max_rule_len) {
    for (unsigned int i = 0; i < max_rule_len; i++) {
        if (rule_ptr[i] == 0) return i;
    }
    return max_rule_len;
}

__kernel void bfs_kernel(
    __global const unsigned char* base_words_in,
    __global const unsigned short* rules_in,
    __global unsigned char* result_buffer,
    const unsigned int num_words,
    const unsigned int num_rules,
    const unsigned int max_word_len,
    const unsigned int max_rule_len_padded,
    const unsigned int max_output_len_padded)
{
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
    for (unsigned int i = 0; i < max_word_len; i++) {
        if (current_word_ptr[i] == 0) {
            word_len = i;
            break;
        }
    }
    
    unsigned int out_len = 0;
    bool changed_flag = false;
    
    // Zero out the result buffer for this thread
    for(unsigned int i = 0; i < max_output_len_padded; i++) {
        result_ptr[i] = 0;
    }

    // --- Unify rule ID blocks (Substituted from Python) ---
    unsigned int start_id_simple = 0; // Placeholder - update with actual values
    unsigned int end_id_simple = start_id_simple + 10; // l, u, c, C, t, r, k, :, d, f
    unsigned int start_id_TD = end_id_simple;
    unsigned int end_id_TD = start_id_TD + 2; // T, D
    unsigned int start_id_s = end_id_TD;
    unsigned int end_id_s = start_id_s + 1; // s
    unsigned int start_id_A = end_id_s;
    unsigned int end_id_A = start_id_A + 3; // ^, $, @
    
    // --- NEW rule ID ranges ---
    unsigned int start_id_groupB = end_id_A;
    unsigned int end_id_groupB = start_id_groupB + 13; // p, {, }, [, ], x, O, i, o, ', z, Z, q
    
    unsigned int start_id_new = end_id_groupB;
    unsigned int end_id_new = start_id_new + 13; // K, *NM, LN, RN, +N, -N, .N, ,N, yN, YN, E, eX, 3NX
    
    // --- Kernel Logic (Rule Transformation) ---
    
    if (rule_id >= start_id_simple && rule_id < end_id_simple) {
        // ... existing simple rules implementation ...
        // (Keep your existing implementation for l, u, c, C, t, r, k, :, d, f)
    }
    else if (rule_id >= start_id_TD && rule_id < end_id_TD) {
        // ... existing T/D rules implementation ...
    }
    else if (rule_id >= start_id_s && rule_id < end_id_s) {
        // ... existing s rules implementation ...
    }
    else if (rule_id >= start_id_A && rule_id < end_id_A) {
        // ... existing Group A rules implementation ...
    }
    else if (rule_id >= start_id_groupB && rule_id < end_id_groupB) {
        // ... existing Group B rules implementation ...
    }
    // --- START NEW RULES IMPLEMENTATION ---
    else if (rule_id >= start_id_new && rule_id < end_id_new) {
        
        // Default to copying the word for modification
        for(unsigned int i = 0; i < word_len; i++) result_ptr[i] = current_word_ptr[i];
        out_len = word_len;

        unsigned char cmd = rule_ptr[0];
        unsigned int N = (rule_len(rule_ptr, max_rule_len_padded) > 1) ? char_to_pos(rule_ptr[1]) : 0xFFFFFFFF;
        unsigned int M = (rule_len(rule_ptr, max_rule_len_padded) > 2) ? char_to_pos(rule_ptr[2]) : 0xFFFFFFFF;
        unsigned char X = (rule_len(rule_ptr, max_rule_len_padded) > 2) ? rule_ptr[2] : 0;
        unsigned char separator = (rule_len(rule_ptr, max_rule_len_padded) > 1) ? rule_ptr[1] : 0;

        if (cmd == 'K') { // 'K' (Swap last two characters)
            if (word_len >= 2) {
                result_ptr[word_len - 1] = current_word_ptr[word_len - 2];
                result_ptr[word_len - 2] = current_word_ptr[word_len - 1];
                changed_flag = true;
            }
        }
        else if (cmd == '*') { // '*NM' (Swap character at position N with character at position M)
            if (N != 0xFFFFFFFF && M != 0xFFFFFFFF && N < word_len && M < word_len && N != M) {
                unsigned char temp = result_ptr[N];
                result_ptr[N] = result_ptr[M];
                result_ptr[M] = temp;
                changed_flag = true;
            }
        }
        else if (cmd == 'L') { // 'LN' (Bitwise shift left character @ N)
            if (N != 0xFFFFFFFF && N < word_len) {
                result_ptr[N] = current_word_ptr[N] << 1;
                changed_flag = true;
            }
        }
        else if (cmd == 'R') { // 'RN' (Bitwise shift right character @ N)
            if (N != 0xFFFFFFFF && N < word_len) {
                result_ptr[N] = current_word_ptr[N] >> 1;
                changed_flag = true;
            }
        }
        else if (cmd == '+') { // '+N' (ASCII increment character @ N by 1)
            if (N != 0xFFFFFFFF && N < word_len) {
                result_ptr[N] = current_word_ptr[N] + 1;
                changed_flag = true;
            }
        }
        else if (cmd == '-') { // '-N' (ASCII decrement character @ N by 1)
            if (N != 0xFFFFFFFF && N < word_len) {
                result_ptr[N] = current_word_ptr[N] - 1;
                changed_flag = true;
            }
        }
        else if (cmd == '.') { // '.N' (Replace character @ N with value at @ N plus 1)
            if (N != 0xFFFFFFFF && N + 1 < word_len) {
                result_ptr[N] = current_word_ptr[N + 1];
                changed_flag = true;
            }
        }
        else if (cmd == ',') { // ',N' (Replace character @ N with value at @ N minus 1)
            if (N != 0xFFFFFFFF && N > 0 && N < word_len) {
                result_ptr[N] = current_word_ptr[N - 1];
                changed_flag = true;
            }
        }
        else if (cmd == 'y') { // 'yN' (Duplicate first N characters)
            if (N != 0xFFFFFFFF && N > 0 && N <= word_len) {
                unsigned int total_len = word_len + N;
                if (total_len < max_output_len_padded) {
                    // Shift original word right by N positions
                    for (int i = word_len - 1; i >= 0; i--) {
                        result_ptr[i + N] = result_ptr[i];
                    }
                    // Duplicate first N characters at the beginning
                    for (unsigned int i = 0; i < N; i++) {
                        result_ptr[i] = current_word_ptr[i];
                    }
                    out_len = total_len;
                    changed_flag = true;
                }
            }
        }
        else if (cmd == 'Y') { // 'YN' (Duplicate last N characters)
            if (N != 0xFFFFFFFF && N > 0 && N <= word_len) {
                unsigned int total_len = word_len + N;
                if (total_len < max_output_len_padded) {
                    // Append last N characters
                    for (unsigned int i = 0; i < N; i++) {
                        result_ptr[word_len + i] = current_word_ptr[word_len - N + i];
                    }
                    out_len = total_len;
                    changed_flag = true;
                }
            }
        }
        else if (cmd == 'E') { // 'E' (Title case)
            // First lowercase everything
            for (unsigned int i = 0; i < word_len; i++) {
                unsigned char c = current_word_ptr[i];
                if (c >= 'A' && c <= 'Z') {
                    result_ptr[i] = c + 32;
                } else {
                    result_ptr[i] = c;
                }
            }
            
            // Then uppercase first letter and letters after spaces
            bool capitalize_next = true;
            for (unsigned int i = 0; i < word_len; i++) {
                if (capitalize_next && result_ptr[i] >= 'a' && result_ptr[i] <= 'z') {
                    result_ptr[i] = result_ptr[i] - 32;
                    changed_flag = true;
                }
                capitalize_next = (result_ptr[i] == ' ');
            }
            out_len = word_len;
        }
        else if (cmd == 'e') { // 'eX' (Title case with custom separator)
            // First lowercase everything
            for (unsigned int i = 0; i < word_len; i++) {
                unsigned char c = current_word_ptr[i];
                if (c >= 'A' && c <= 'Z') {
                    result_ptr[i] = c + 32;
                } else {
                    result_ptr[i] = c;
                }
            }
            
            // Then uppercase first letter and letters after custom separator
            bool capitalize_next = true;
            for (unsigned int i = 0; i < word_len; i++) {
                if (capitalize_next && result_ptr[i] >= 'a' && result_ptr[i] <= 'z') {
                    result_ptr[i] = result_ptr[i] - 32;
                    changed_flag = true;
                }
                capitalize_next = (result_ptr[i] == separator);
            }
            out_len = word_len;
        }
        else if (cmd == '3') { // '3NX' (Toggle case after Nth instance of separator char)
            unsigned int separator_count = 0;
            unsigned int target_count = N;
            unsigned char sep_char = X;
            
            if (target_count != 0xFFFFFFFF) {
                for (unsigned int i = 0; i < word_len; i++) {
                    if (current_word_ptr[i] == sep_char) {
                        separator_count++;
                        if (separator_count == target_count && i + 1 < word_len) {
                            // Toggle the case of the character after the separator
                            unsigned char c = current_word_ptr[i + 1];
                            if (c >= 'a' && c <= 'z') {
                                result_ptr[i + 1] = c - 32;
                                changed_flag = true;
                            } else if (c >= 'A' && c <= 'Z') {
                                result_ptr[i + 1] = c + 32;
                                changed_flag = true;
                            }
                            break;
                        }
                    }
                }
            }
        }
    }
    // --- END NEW RULES IMPLEMENTATION ---
    
    // Final output processing
    if (changed_flag && out_len > 0) {
        if (out_len < max_output_len_padded) {
            result_ptr[out_len] = 0; // Null terminator
        }
    } else {
        // If the word was not changed or rule execution failed/resulted in length 0, zero out the output
        for (unsigned int i = 0; i < max_output_len_padded; i++) {
            result_ptr[i] = 0;
        }
    }
}
