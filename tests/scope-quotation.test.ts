import test from 'node:test';
import assert from 'node:assert/strict';
import {correctionErrors} from '../src/grading.ts';
import {assessment,family} from './fixtures.ts';
test('canonical quotation repair changes only literal registry text and never comparison decisions',()=>{
 const registry=family();const previous=assessment(5);previous.outcomes[0]!.family_comparisons=[{family_id:registry.id,existing_scope:'Paraphrased old scope',relationship:'distinct_outcome',reason:'Different experiment and acceptance test'}];
 const fixed=structuredClone(previous);fixed.outcomes[0]!.family_comparisons![0]!.existing_scope=registry.scope;
 assert.deepEqual(correctionErrors(previous,fixed,[registry]),[]);
 assert.ok(correctionErrors(previous,fixed).length);
 for(const patch of [{family_id:'other'},{existing_scope:'invented'},{relationship:'same_outcome'},{reason:'changed decision'}]){
  const changed=structuredClone(fixed);Object.assign(changed.outcomes[0]!.family_comparisons![0],patch);
  assert.ok(correctionErrors(previous,changed,[registry]).length);
 }
 const increased=structuredClone(fixed);increased.outcomes[0]!.assessed_tier=10;assert.ok(correctionErrors(previous,increased,[registry]).length);
 const missing=structuredClone(fixed);missing.outcomes[0]!.family_comparisons=[];assert.ok(correctionErrors(previous,missing,[registry]).length);
});
