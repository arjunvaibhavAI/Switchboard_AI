#include <stdio.h>
#include <string.h>

// CROSS-PLATFORM EXPORT MACRO
#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif

EXPORT int analyze_and_redact(char* text) {
    if (text == NULL) return 0;
    
    int len = (int)strlen(text);
    int risk_found = 0;
    int digit_count = 0;

    for (int i = 0; i < len; i++) {
        // --- 1. Detect & Redact Credit Cards  ---
        if (text[i] >= '0' && text[i] <= '9') {
            digit_count++;
            if (digit_count >= 13) { 
                // Redact backward to mask the entire sequence
                for (int j = 0; j < digit_count; j++) {
                    if (text[i-j] >= '0' && text[i-j] <= '9') text[i-j] = '*';
                }
                risk_found = 1;
            }
        } else if (text[i] != ' ' && text[i] != '-') {
            digit_count = 0;
        }

        // --- 2. Detect & Redact API Keys (sk-...) ---
        if (i + 3 < len && text[i] == 's' && text[i+1] == 'k' && text[i+2] == '-') {
            int k = i + 3;
            while (k < len && text[k] != ' ' && text[k] != '\n') {
                text[k] = '*'; 
                k++;
            }
            risk_found = 1;
        }
    }
    return risk_found;
}