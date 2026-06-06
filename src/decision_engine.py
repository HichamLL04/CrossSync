def parse_dtw_path(path: list[tuple[int, int]]) -> list[dict]:
    # Map A indices to lists of B indices and vice versa
    a_to_b = {}
    b_to_a = {}
    for u, v in path:
        a_to_b.setdefault(u, []).append(v)
        b_to_a.setdefault(v, []).append(u)

    groups = []
    visited_a = set()
    
    # Grouping connected components in the alignment graph sequentially
    for u in sorted(a_to_b.keys()):
        if u in visited_a:
            continue
        
        # Find all connected A and B indices
        connected_a = {u}
        connected_b = set(a_to_b[u])
        
        # Expand connection group
        changed = True
        while changed:
            changed = False
            # Add all A that map to any current B
            new_a = set()
            for b in connected_b:
                new_a.update(b_to_a[b])
            if not new_a.issubset(connected_a):
                connected_a.update(new_a)
                changed = True
            
            # Add all B that map to any current A
            new_b = set()
            for a in connected_a:
                new_b.update(a_to_b[a])
            if not new_b.issubset(connected_b):
                connected_b.update(new_b)
                changed = True

        visited_a.update(connected_a)
        
        src = sorted(list(connected_a))
        tgt = sorted(list(connected_b))
        
        if len(src) == 1 and len(tgt) == 1:
            gtype = "keep"
        elif len(src) == 1 and len(tgt) > 1:
            gtype = "split"
        else:
            gtype = "join"
            
        groups.append({
            "type": gtype,
            "source_indices": src,
            "target_indices": tgt
        })
    return groups
