import { mkdir, writeFile } from 'node:fs/promises';
import { contributionSchema, directionSchema, artifactSchema, assessmentSchema, decisionSchema, decisionRecordSchema, profileSchema } from '../src/validation.ts';
import { DEFAULT_PROFILE, STAGE_PROMPTS, SYSTEM_PROMPT } from '../src/grading.ts';
await mkdir('schemas', { recursive: true }); await mkdir('grading/prompts', { recursive: true }); await mkdir('grading/profiles', { recursive: true });
for (const [name, schema] of Object.entries({ contribution: contributionSchema, direction: directionSchema, artifact: artifactSchema, assessment: assessmentSchema, decision: decisionSchema, 'decision-record': decisionRecordSchema, profile: profileSchema })) await writeFile(`schemas/${name}-v1.json`, JSON.stringify(schema, null, 2) + '\n');
await writeFile('grading/profiles/voynich-claude-subscription-0.1.json', JSON.stringify(DEFAULT_PROFILE, null, 2) + '\n');
await writeFile('grading/profiles/active.json', JSON.stringify(DEFAULT_PROFILE, null, 2) + '\n');
await writeFile('grading/prompts/system.md', SYSTEM_PROMPT + '\n');
for (const [stage, prompt] of Object.entries(STAGE_PROMPTS)) await writeFile(`grading/prompts/${stage}.md`, prompt + '\n');
