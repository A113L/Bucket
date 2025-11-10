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

// Helper function to check if character is a vowel
bool is_vowel(unsigned char c) {
    return (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || 
            c == 'A' || c == 'E' || c == 'I' || c == 'O' || c == 'U');
}

// Helper function to check if character is a consonant
bool is_consonant(unsigned char c) {
    return ((c >= 'a' && c <= 'z' && !is_vowel(c)) || 
            (c >= 'A' && c <= 'Z' && !is_vowel(c)));
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

    // --- Unify rule ID blocks ---
    unsigned int start_id_simple = 0;
    unsigned int end_id_simple = start_id_simple + 10; // l, u, c, C, t, r, k, :, d, f
    unsigned int start_id_TD = end_id_simple;
    unsigned int end_id_TD = start_id_TD + 2; // T, D
    unsigned int start_id_s = end_id_TD;
    unsigned int end_id_s = start_id_s + 1; // s
    unsigned int start_id_A = end_id_s;
    unsigned int end_id_A = start_id_A + 3; // ^, $, @
    
    unsigned int start_id_groupB = end_id_A;
    unsigned int end_id_groupB = start_id_groupB + 13; // p, {, }, [, ], x, O, i, o, ', z, Z, q
    
    unsigned int start_id_new = end_id_groupB;
    unsigned int end_id_new = start_id_new + 13; // K, *NM, LN, RN, +N, -N, .N, ,N, yN, YN, E, eX, 3NX
    
    // --- COMPREHENSIVE ALPHABET VOWEL RULES IMPLEMENTATION ---
    unsigned int start_id_vowel = end_id_new;
    unsigned int end_id_vowel = start_id_vowel + 100; // Extended range for all vowel variations
    
    if (rule_id >= start_id_vowel && rule_id < end_id_vowel) {
        unsigned char cmd = rule_ptr[0]; // Should be 'v'
        unsigned int vowel_index = rule_id - start_id_vowel;
        
        // Define comprehensive vowel sequences and special characters
        unsigned char vowels_lower[] = {'a', 'e', 'i', 'o', 'u'};
        unsigned char vowels_upper[] = {'A', 'E', 'I', 'O', 'U'};
        unsigned char vowels_all[] = {'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U'};
        unsigned char vowels_extended[] = {'a', 'e', 'i', 'o', 'u', 'y', 'w', 'A', 'E', 'I', 'O', 'U', 'Y', 'W'};
        
        // Comprehensive special characters including all keyboard symbols
        unsigned char special_chars[] = {
            '_', '.', ',', ':', ';', '-', '=', '+', '*', '/', '\\', 
            '|', '!', '@', '#', '$', '%', '^', '&', '(', ')', 
            '[', ']', '{', '}', '<', '>', '?', '~', '`', '"', '\'',
            ' ', '\t', '\n', '\r', '\v', '\f', // whitespace characters
            '§', '©', '®', '™', '°', '·', '•', '¶', // extended symbols
            '±', '¼', '½', '¾', '×', '÷', // mathematical symbols
            '¡', '¿', '€', '£', '¥', '¢', '¤', '¦', // currency and punctuation
            '¨', '´', '`', 'ˆ', '˜', '¯', '˘', '˙', '˚', '¸', '˝', '˛', 'ˇ' // diacritics
        };
        
        // Alphabet sequences for advanced patterns
        unsigned char alphabet_lower[] = {
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
        };
        
        unsigned char alphabet_upper[] = {
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
        };
        
        unsigned char numbers[] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'};
        
        unsigned char insert_char = 0;
        bool use_sequence = false;
        unsigned int sequence_type = 0;
        unsigned int sequence_index = 0;
        
        // Determine which character/sequence to insert based on the rule index
        if (vowel_index < 10) {
            // v0-v9: insert specific vowel from vowels_all
            insert_char = vowels_all[vowel_index % 10];
        } 
        else if (vowel_index < 36) {
            // vA-vZ: insert vowels in sequence (A=10, B=11, etc.)
            unsigned int seq_index = vowel_index - 10;
            insert_char = vowels_lower[seq_index % 5];
        }
        else if (vowel_index < 68) {
            // Special characters range (v_ to extended symbols)
            unsigned int special_index = vowel_index - 36;
            if (special_index < 64) {
                insert_char = special_chars[special_index % 64];
            } else {
                insert_char = '_'; // fallback
            }
        }
        else if (vowel_index < 94) {
            // Alphabet sequences (va-vz)
            unsigned int alpha_index = vowel_index - 68;
            if (alpha_index < 26) {
                insert_char = alphabet_lower[alpha_index];
                use_sequence = true;
                sequence_type = 1; // lowercase alphabet
            }
        }
        else if (vowel_index < 100) {
            // Number sequences (v0a-v9a)
            unsigned int num_index = vowel_index - 94;
            if (num_index < 10) {
                insert_char = numbers[num_index];
                use_sequence = true;
                sequence_type = 2; // numbers
            }
        }
        else {
            // Advanced vowel sequences and patterns
            use_sequence = true;
            sequence_type = vowel_index - 100;
        }
        
        // Count consonants in the word
        unsigned int consonant_count = 0;
        for (unsigned int i = 0; i < word_len; i++) {
            if (is_consonant(current_word_ptr[i])) {
                consonant_count++;
            }
        }
        
        if (consonant_count > 0) {
            // Calculate maximum possible output length
            unsigned int max_possible_len = word_len + consonant_count;
            
            if (max_possible_len < max_output_len_padded) {
                unsigned int out_idx = 0;
                unsigned int consonant_counter = 0;
                
                if (!use_sequence) {
                    // Single character insertion
                    for (unsigned int i = 0; i < word_len; i++) {
                        unsigned char c = current_word_ptr[i];
                        
                        // Copy current character
                        result_ptr[out_idx++] = c;
                        
                        // Insert character after consonants
                        if (is_consonant(c)) {
                            result_ptr[out_idx++] = insert_char;
                        }
                    }
                } else {
                    // Advanced sequence insertion
                    for (unsigned int i = 0; i < word_len; i++) {
                        unsigned char c = current_word_ptr[i];
                        
                        // Copy current character
                        result_ptr[out_idx++] = c;
                        
                        // Insert sequence character after consonants
                        if (is_consonant(c)) {
                            // Determine which character to insert based on sequence type
                            switch (sequence_type) {
                                case 0: // Default alternating vowels
                                    result_ptr[out_idx++] = vowels_lower[consonant_counter % 5];
                                    break;
                                case 1: // Alphabet sequence (va-vz)
                                    result_ptr[out_idx++] = alphabet_lower[consonant_counter % 26];
                                    break;
                                case 2: // Number sequence (v0a-v9a)
                                    result_ptr[out_idx++] = numbers[consonant_counter % 10];
                                    break;
                                case 3: // Alternating uppercase vowels
                                    result_ptr[out_idx++] = vowels_upper[consonant_counter % 5];
                                    break;
                                case 4: // Alternating uppercase alphabet
                                    result_ptr[out_idx++] = alphabet_upper[consonant_counter % 26];
                                    break;
                                case 5: // Extended vowels (including y,w)
                                    result_ptr[out_idx++] = vowels_extended[consonant_counter % 14];
                                    break;
                                case 6: // Reverse alphabet
                                    result_ptr[out_idx++] = alphabet_lower[25 - (consonant_counter % 26)];
                                    break;
                                case 7: // Binary pattern 0101
                                    result_ptr[out_idx++] = (consonant_counter % 2 == 0) ? '0' : '1';
                                    break;
                                case 8: // Vowel-consonant pattern
                                    result_ptr[out_idx++] = (consonant_counter % 2 == 0) ? 
                                                           vowels_lower[consonant_counter % 5] : 
                                                           alphabet_lower[consonant_counter % 21];
                                    break;
                                case 9: // Special character sequence
                                    result_ptr[out_idx++] = special_chars[consonant_counter % 32];
                                    break;
                                default: // fallback to alternating vowels
                                    result_ptr[out_idx++] = vowels_lower[consonant_counter % 5];
                                    break;
                            }
                            consonant_counter++;
                        }
                    }
                }
                
                out_len = out_idx;
                changed_flag = true;
            }
        }
        
        // Special case: Empty word handling
        if (word_len == 0) {
            // For empty words, some rules might want to insert the character alone
            if (max_output_len_padded >= 1) {
                if (!use_sequence) {
                    result_ptr[0] = insert_char;
                    out_len = 1;
                    changed_flag = true;
                } else {
                    // For sequences with empty words, insert first sequence character
                    switch (sequence_type) {
                        case 0:
                            result_ptr[0] = vowels_lower[0];
                            break;
                        case 1:
                            result_ptr[0] = alphabet_lower[0];
                            break;
                        case 2:
                            result_ptr[0] = numbers[0];
                            break;
                        default:
                            result_ptr[0] = vowels_lower[0];
                            break;
                    }
                    out_len = 1;
                    changed_flag = true;
                }
            }
        }
    }
    // --- SIMPLE RULES IMPLEMENTATION ---
    else if (rule_id >= start_id_simple && rule_id < end_id_simple) {
        unsigned char cmd = rule_ptr[0];
        
        // Copy the word first
        for(unsigned int i = 0; i < word_len; i++) {
            result_ptr[i] = current_word_ptr[i];
        }
        out_len = word_len;
        
        if (cmd == 'l') { // Lowercase all
            for(unsigned int i = 0; i < word_len; i++) {
                unsigned char c = result_ptr[i];
                if (c >= 'A' && c <= 'Z') {
                    result_ptr[i] = c + 32;
                    changed_flag = true;
                }
            }
        }
        else if (cmd == 'u') { // Uppercase all
            for(unsigned int i = 0; i < word_len; i++) {
                unsigned char c = result_ptr[i];
                if (c >= 'a' && c <= 'z') {
                    result_ptr[i] = c - 32;
                    changed_flag = true;
                }
            }
        }
        else if (cmd == 'c') { // Capitalize first letter
            if (word_len > 0) {
                unsigned char c = result_ptr[0];
                if (c >= 'a' && c <= 'z') {
                    result_ptr[0] = c - 32;
                    changed_flag = true;
                }
            }
        }
        else if (cmd == 'C') { // Lowercase first letter
            if (word_len > 0) {
                unsigned char c = result_ptr[0];
                if (c >= 'A' && c <= 'Z') {
                    result_ptr[0] = c + 32;
                    changed_flag = true;
                }
            }
        }
        else if (cmd == 't') { // Toggle case
            for(unsigned int i = 0; i < word_len; i++) {
                unsigned char c = result_ptr[i];
                if (c >= 'a' && c <= 'z') {
                    result_ptr[i] = c - 32;
                    changed_flag = true;
                } else if (c >= 'A' && c <= 'Z') {
                    result_ptr[i] = c + 32;
                    changed_flag = true;
                }
            }
        }
        else if (cmd == 'r') { // Reverse
            for(unsigned int i = 0; i < word_len; i++) {
                result_ptr[i] = current_word_ptr[word_len - 1 - i];
            }
            changed_flag = true;
        }
        else if (cmd == 'k') { // Duplicate
            if (word_len * 2 <= max_output_len_padded) {
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[word_len + i] = current_word_ptr[i];
                }
                out_len = word_len * 2;
                changed_flag = true;
            }
        }
        else if (cmd == ':') { // Duplicate and reverse
            if (word_len * 2 <= max_output_len_padded) {
                // Duplicate
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[word_len + i] = current_word_ptr[i];
                }
                // Reverse the duplicate
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[word_len + i] = current_word_ptr[word_len - 1 - i];
                }
                out_len = word_len * 2;
                changed_flag = true;
            }
        }
        else if (cmd == 'd') { // Duplicate with space
            if (word_len * 2 + 1 <= max_output_len_padded) {
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[i] = current_word_ptr[i];
                    result_ptr[word_len + 1 + i] = current_word_ptr[i];
                }
                result_ptr[word_len] = ' ';
                out_len = word_len * 2 + 1;
                changed_flag = true;
            }
        }
        else if (cmd == 'f') { // Duplicate and reverse with space
            if (word_len * 2 + 1 <= max_output_len_padded) {
                // Copy original
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[i] = current_word_ptr[i];
                }
                // Add space
                result_ptr[word_len] = ' ';
                // Add reversed
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[word_len + 1 + i] = current_word_ptr[word_len - 1 - i];
                }
                out_len = word_len * 2 + 1;
                changed_flag = true;
            }
        }
    }
    // --- T/D RULES IMPLEMENTATION ---
    else if (rule_id >= start_id_TD && rule_id < end_id_TD) {
        unsigned char cmd = rule_ptr[0];
        
        // Copy the word first
        for(unsigned int i = 0; i < word_len; i++) {
            result_ptr[i] = current_word_ptr[i];
        }
        out_len = word_len;
        
        if (cmd == 'T') { // Toggle at position N
            unsigned int N = (rule_len(rule_ptr, max_rule_len_padded) > 1) ? char_to_pos(rule_ptr[1]) : 0xFFFFFFFF;
            if (N != 0xFFFFFFFF && N < word_len) {
                unsigned char c = result_ptr[N];
                if (c >= 'a' && c <= 'z') {
                    result_ptr[N] = c - 32;
                    changed_flag = true;
                } else if (c >= 'A' && c <= 'Z') {
                    result_ptr[N] = c + 32;
                    changed_flag = true;
                }
            }
        }
        else if (cmd == 'D') { // Delete at position N
            unsigned int N = (rule_len(rule_ptr, max_rule_len_padded) > 1) ? char_to_pos(rule_ptr[1]) : 0xFFFFFFFF;
            if (N != 0xFFFFFFFF && N < word_len) {
                for(unsigned int i = N; i < word_len - 1; i++) {
                    result_ptr[i] = result_ptr[i + 1];
                }
                out_len = word_len - 1;
                changed_flag = true;
            }
        }
    }
    // --- S RULES IMPLEMENTATION ---
    else if (rule_id >= start_id_s && rule_id < end_id_s) {
        unsigned char cmd = rule_ptr[0];
        unsigned int rule_length = rule_len(rule_ptr, max_rule_len_padded);
        
        if (rule_length >= 3) { // Need at least sXY
            unsigned char find_char = rule_ptr[1];
            unsigned char replace_char = rule_ptr[2];
            
            // Copy the word first
            for(unsigned int i = 0; i < word_len; i++) {
                result_ptr[i] = current_word_ptr[i];
                if (current_word_ptr[i] == find_char) {
                    result_ptr[i] = replace_char;
                    changed_flag = true;
                }
            }
            out_len = word_len;
        }
    }
    // --- GROUP A RULES IMPLEMENTATION ---
    else if (rule_id >= start_id_A && rule_id < end_id_A) {
        unsigned char cmd = rule_ptr[0];
        
        if (cmd == '^') { // Prepend
            unsigned char prepend_char = (rule_len(rule_ptr, max_rule_len_padded) > 1) ? rule_ptr[1] : 0;
            if (prepend_char != 0 && word_len + 1 < max_output_len_padded) {
                result_ptr[0] = prepend_char;
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[i + 1] = current_word_ptr[i];
                }
                out_len = word_len + 1;
                changed_flag = true;
            }
        }
        else if (cmd == '$') { // Append
            unsigned char append_char = (rule_len(rule_ptr, max_rule_len_padded) > 1) ? rule_ptr[1] : 0;
            if (append_char != 0 && word_len + 1 < max_output_len_padded) {
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[i] = current_word_ptr[i];
                }
                result_ptr[word_len] = append_char;
                out_len = word_len + 1;
                changed_flag = true;
            }
        }
        else if (cmd == '@') { // Delete all instances of X
            unsigned char delete_char = (rule_len(rule_ptr, max_rule_len_padded) > 1) ? rule_ptr[1] : 0;
            if (delete_char != 0) {
                unsigned int out_idx = 0;
                for(unsigned int i = 0; i < word_len; i++) {
                    if (current_word_ptr[i] != delete_char) {
                        result_ptr[out_idx++] = current_word_ptr[i];
                    } else {
                        changed_flag = true;
                    }
                }
                out_len = out_idx;
            }
        }
    }
    // --- GROUP B RULES IMPLEMENTATION ---
    else if (rule_id >= start_id_groupB && rule_id < end_id_groupB) {
        unsigned char cmd = rule_ptr[0];
        unsigned int N = (rule_len(rule_ptr, max_rule_len_padded) > 1) ? char_to_pos(rule_ptr[1]) : 0xFFFFFFFF;
        
        // Copy the word first
        for(unsigned int i = 0; i < word_len; i++) {
            result_ptr[i] = current_word_ptr[i];
        }
        out_len = word_len;
        
        if (cmd == 'p') { // Pluralize
            if (word_len + 1 < max_output_len_padded) {
                result_ptr[word_len] = 's';
                out_len = word_len + 1;
                changed_flag = true;
            }
        }
        else if (cmd == '{') { // Rotate left
            if (word_len > 1) {
                unsigned char first_char = result_ptr[0];
                for(unsigned int i = 0; i < word_len - 1; i++) {
                    result_ptr[i] = result_ptr[i + 1];
                }
                result_ptr[word_len - 1] = first_char;
                changed_flag = true;
            }
        }
        else if (cmd == '}') { // Rotate right
            if (word_len > 1) {
                unsigned char last_char = result_ptr[word_len - 1];
                for(int i = word_len - 1; i > 0; i--) {
                    result_ptr[i] = result_ptr[i - 1];
                }
                result_ptr[0] = last_char;
                changed_flag = true;
            }
        }
        else if (cmd == '[') { // Delete first character
            if (word_len > 1) {
                for(unsigned int i = 0; i < word_len - 1; i++) {
                    result_ptr[i] = current_word_ptr[i + 1];
                }
                out_len = word_len - 1;
                changed_flag = true;
            }
        }
        else if (cmd == ']') { // Delete last character
            if (word_len > 1) {
                out_len = word_len - 1;
                changed_flag = true;
            }
        }
        else if (cmd == 'x') { // Extract range N-M
            unsigned int M = (rule_len(rule_ptr, max_rule_len_padded) > 2) ? char_to_pos(rule_ptr[2]) : 0xFFFFFFFF;
            if (N != 0xFFFFFFFF && M != 0xFFFFFFFF && N <= M && M < word_len) {
                unsigned int out_idx = 0;
                for(unsigned int i = N; i <= M; i++) {
                    result_ptr[out_idx++] = current_word_ptr[i];
                }
                out_len = out_idx;
                changed_flag = true;
            }
        }
        else if (cmd == 'O') { // Overstrike at position N
            unsigned char overstrike_char = (rule_len(rule_ptr, max_rule_len_padded) > 2) ? rule_ptr[2] : 0;
            if (N != 0xFFFFFFFF && overstrike_char != 0 && N < word_len) {
                result_ptr[N] = overstrike_char;
                changed_flag = true;
            }
        }
        else if (cmd == 'i') { // Insert at position N
            unsigned char insert_char = (rule_len(rule_ptr, max_rule_len_padded) > 2) ? rule_ptr[2] : 0;
            if (N != 0xFFFFFFFF && insert_char != 0 && word_len + 1 < max_output_len_padded && N <= word_len) {
                // Shift characters right
                for(int i = word_len; i > N; i--) {
                    result_ptr[i] = result_ptr[i - 1];
                }
                result_ptr[N] = insert_char;
                out_len = word_len + 1;
                changed_flag = true;
            }
        }
        else if (cmd == 'o') { // Overwrite at position N
            unsigned char overwrite_char = (rule_len(rule_ptr, max_rule_len_padded) > 2) ? rule_ptr[2] : 0;
            if (N != 0xFFFFFFFF && overwrite_char != 0 && N < word_len) {
                result_ptr[N] = overwrite_char;
                changed_flag = true;
            }
        }
        else if (cmd == '\'') { // Increment at position N
            if (N != 0xFFFFFFFF && N < word_len) {
                result_ptr[N] = current_word_ptr[N] + 1;
                changed_flag = true;
            }
        }
        else if (cmd == 'z') { // Duplicate first character
            if (word_len + 1 < max_output_len_padded) {
                // Shift right
                for(int i = word_len; i > 0; i--) {
                    result_ptr[i] = result_ptr[i - 1];
                }
                result_ptr[0] = current_word_ptr[0];
                out_len = word_len + 1;
                changed_flag = true;
            }
        }
        else if (cmd == 'Z') { // Duplicate last character
            if (word_len + 1 < max_output_len_padded) {
                result_ptr[word_len] = current_word_ptr[word_len - 1];
                out_len = word_len + 1;
                changed_flag = true;
            }
        }
        else if (cmd == 'q') { // Duplicate all characters
            if (word_len * 2 < max_output_len_padded) {
                unsigned int out_idx = 0;
                for(unsigned int i = 0; i < word_len; i++) {
                    result_ptr[out_idx++] = current_word_ptr[i];
                    result_ptr[out_idx++] = current_word_ptr[i];
                }
                out_len = word_len * 2;
                changed_flag = true;
            }
        }
    }
    // --- NEW RULES IMPLEMENTATION ---
    else if (rule_id >= start_id_new && rule_id < end_id_new) {
        // Copy the word first
        for(unsigned int i = 0; i < word_len; i++) {
            result_ptr[i] = current_word_ptr[i];
        }
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
