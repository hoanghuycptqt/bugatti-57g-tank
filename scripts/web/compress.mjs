import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, draco } from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';
const [inp, out, qp = '16', qn = '12'] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'draco3d.decoder': await draco3d.createDecoderModule(),
  'draco3d.encoder': await draco3d.createEncoderModule(),
});
const doc = await io.read(inp);
await doc.transform(dedup(), prune(), draco({ method: 'edgebreaker', encodeSpeed: 3, decodeSpeed: 5,
  quantizePosition: +qp, quantizeNormal: +qn, quantizeTexcoord: 12, quantizationVolume: 'scene' }));
await io.write(out, doc);
console.log('written', out);
