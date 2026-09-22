"""Background renderer for the 57G Tank scene.
usage (from the repo root): blender -b Bugatti_57G_Tank.blend -P scripts/render/render_final.py -- scripts/render/jobs_final.json
Each job: {"cam": name, "res": [w, h], "spp": int, "out": "path/without_ext"} (relative paths are taken from the current folder)
Renders RGBA (shadow-catcher floor, transparent film) and composites it over pure white."""
import bpy, sys, json, os, time
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
jobs = json.load(open(argv[0]))
for j in jobs:
    j['out'] = os.path.abspath(j['out'])
os.makedirs(os.path.dirname(jobs[0]['out']), exist_ok=True)
sc = bpy.context.scene
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = (d.type == 'METAL')
    sc.cycles.device = 'GPU'
except Exception as e:
    print('GPU setup failed:', e)
sc.render.use_persistent_data = True
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '8'
log = open(os.path.join(os.path.dirname(jobs[0]['out']), 'render_log.txt'), 'a')
for job in jobs:
    t0 = time.time()
    sc.camera = bpy.data.objects[job['cam']]
    sc.render.resolution_x, sc.render.resolution_y = job['res']
    sc.render.resolution_percentage = 100
    sc.cycles.samples = job.get('spp', 256)
    raw = job['out'] + '_rgba.png'
    sc.render.filepath = raw
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(raw)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    px = np.empty(w*h*4, np.float32); img.pixels.foreach_get(px); px = px.reshape(-1, 4)
    a = px[:, 3:4]
    rgb = px[:, :3]*a + (1.0 - a)
    out = bpy.data.images.new(os.path.basename(job['out']), w, h, alpha=False)
    out.colorspace_settings.name = 'Non-Color'
    o = np.concatenate([rgb, np.ones((len(rgb), 1), np.float32)], 1).astype(np.float32)
    out.pixels.foreach_set(o.ravel())
    out.filepath_raw = job['out'] + '.png'; out.file_format = 'PNG'; out.save()
    out.filepath_raw = job['out'] + '.jpg'; out.file_format = 'JPEG'
    try:
        out.save(quality=95)
    except TypeError:
        out.save()
    bpy.data.images.remove(img); bpy.data.images.remove(out)
    msg = '%s done in %.1fs\n' % (job['out'], time.time() - t0)
    print(msg); log.write(msg); log.flush()
log.write('ALL DONE\n'); log.close()
