from pathlib import Path
p=Path('pipeline/lib/clips.py');s=p.read_text(encoding='utf-8');s=s.replace('target, pole, end_rot: Matrix = None):','target, pole, end_rot: Matrix = None, min_mid_z: float = None):',1);s=s.replace('        Keys upper/lower (and end if end_rot). Returns','        min_mid_z optionally constrains the elbow/knee centre above a floor while preserving segment lengths.\n        Keys upper/lower (and end if end_rot). Returns',1);s=s.replace('        mid = p0 + direction * a + perp * h\n','''        center = p0 + direction * a
        mid = center + perp * h
        if min_mid_z is not None and mid.z < min_mid_z and h > 1e-6:
            # The joint lies on a circle perpendicular to the hip->ankle axis.
            # Choose the closest bend direction on that circle above the floor.
            up = Vector((0, 0, 1)) - direction * direction.z
            span = up.length
            if span > 1e-6:
                up.normalize()
                tangent = direction.cross(up).normalized()
                height = max(-1.0, min(1.0, (min_mid_z - center.z) / (h * span)))
                sign = 1.0 if perp.dot(tangent) >= 0 else -1.0
                perp = up * height + tangent * (sign * math.sqrt(max(0.0, 1 - height * height)))
                mid = center + perp * h
''',1);p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
p=Path('pipeline/lib/posekeys.py');s=p.read_text(encoding='utf-8');s=s.replace('miss = clip.ik(f, *chain, tpos + Vector(p[f"foot_{side}"]), knee, end_rot=rot)','miss = clip.ik(f, *chain, tpos + Vector(p[f"foot_{side}"]), knee, end_rot=rot,\n                           min_mid_z=floor + clip.knee_clearance if hasattr(clip, "knee_clearance") else None)',1);p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
p=Path('pipeline/clip_defs/volleyball.py');s=p.read_text(encoding='utf-8').replace('    worst = pk.animate(c, keys)','    if variant == "vb_dive":\n        c.knee_clearance = 0.065  # knee centre: leave room for the mesh at ground contact\n    worst = pk.animate(c, keys)',1);a=s.index('def dive():');b=s.index('\n\ndef shuffle_R()',a);d=s[a:b].replace('"pelvis": (66, 0, 0)','"pelvis": (45, 0, 0)').replace('"pelvis": (24, 0, 0), "spine": (68','"pelvis": (16, 0, 0), "spine": (68');s=s[:a]+d+s[b:];p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
