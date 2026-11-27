import re
import sys
import os

def minify_lua_source(src, header=""):
    pos = 0
    length = len(src)
    tokens = []
    
    while pos < length:
        # String single/double quote
        if src[pos] in ('"', "'"):
            q = src[pos]
            start = pos
            pos += 1
            while pos < length:
                if src[pos] == '\\':
                    pos += 2
                elif src[pos] == q:
                    pos += 1
                    break
                else:
                    pos += 1
            tokens.append(('STR', src[start:pos]))
        # Multiline comment
        elif src[pos:pos+4] == '--[[' or re.match(r'^--\[=*\[', src[pos:pos+10]):
            m = re.match(r'^--\[(=*)\[', src[pos:])
            eq = m.group(1)
            closer = ']' + eq + ']'
            end_pos = src.find(closer, pos + len(m.group(0)))
            if end_pos != -1:
                pos = end_pos + len(closer)
            else:
                pos = length
            tokens.append(('WS', ' '))
        # Single line comment
        elif src[pos:pos+2] == '--':
            nl = src.find('\n', pos)
            if nl != -1:
                pos = nl
            else:
                pos = length
        # Multiline string
        elif re.match(r'^\[=*\[', src[pos:pos+10]):
            m = re.match(r'^\[(=*)\[', src[pos:])
            eq = m.group(1)
            closer = ']' + eq + ']'
            end_pos = src.find(closer, pos + len(m.group(0)))
            if end_pos != -1:
                end_idx = end_pos + len(closer)
                tokens.append(('STR', src[pos:end_idx]))
                pos = end_idx
            else:
                tokens.append(('STR', src[pos:]))
                pos = length
        # Newline
        elif src[pos] == '\n':
            tokens.append(('NL', '\n'))
            pos += 1
        # Whitespace
        elif src[pos] in (' ', '\t', '\r'):
            tokens.append(('WS', ' '))
            pos += 1
        else:
            start = pos
            if src[pos].isalnum() or src[pos] == '_':
                while pos < length and (src[pos].isalnum() or src[pos] == '_'):
                    pos += 1
                tokens.append(('WORD', src[start:pos]))
            else:
                pos += 1
                tokens.append(('SYM', src[start:pos]))

    output = []
    if header.strip():
        output.append(header.strip())
        
    line_buf = []
    prev_type = None
    prev_val = None
    
    for t_type, t_val in tokens:
        if t_type == 'NL':
            if line_buf:
                line_str = ''.join(line_buf).strip()
                if line_str:
                    output.append(line_str)
                line_buf = []
            prev_type = 'NL'
            prev_val = '\n'
            continue
            
        if t_type == 'WS':
            if prev_type in ('WORD', 'STR') and t_val == ' ':
                prev_type = 'WS_PENDING'
            continue
            
        if t_type == 'WORD':
            if prev_type in ('WORD', 'WS_PENDING'):
                line_buf.append(' ')
            line_buf.append(t_val)
            prev_type = 'WORD'
            prev_val = t_val
        elif t_type == 'STR':
            if prev_type == 'WS_PENDING':
                line_buf.append(' ')
            line_buf.append(t_val)
            prev_type = 'STR'
            prev_val = t_val
        elif t_type == 'SYM':
            if t_val == '-' and prev_val == '-':
                line_buf.append(' ')
            line_buf.append(t_val)
            prev_type = 'SYM'
            prev_val = t_val

    if line_buf:
        line_str = ''.join(line_buf).strip()
        if line_str:
            output.append(line_str)
            
    return '\n'.join(output)

if __name__ == '__main__':
    in_file = sys.argv[1] if len(sys.argv) > 1 else 'scratch/v54_raw.lua'
    out_file = sys.argv[2] if len(sys.argv) > 2 else 'FishingHelper'
    header = '-- ZeluxHub · River Hunter [Optimized & Minified Production Build]'
    
    with open(in_file, 'r', encoding='utf-8') as f:
        src = f.read()
        
    res = minify_lua_source(src, header)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(res)
        
    print(f'Successfully minified {in_file} -> {out_file}: {len(src)} bytes to {len(res)} bytes ({len(src.splitlines())} lines -> {len(res.splitlines())} lines)')
