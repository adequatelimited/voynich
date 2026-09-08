# Large artifact review runtime

Profile v11 retains the v10 scoring methodology, Sonnet model, prompts, input/output bounds and four-stage maximum. The per-stage runtime ceiling increases from 180 to 600 seconds so a large artifact review can return its complete structured response. Aggregate operating ceilings and single-active-job limits remain enforced. The completed historical regrade cohort is closed; this release does not authorize repeated grading of successfully scored submissions.

PR13's v10 adjudication terminated at its 180-second runtime ceiling without returning an assessment. Its full reserved exposure is retained during authenticated runner reconciliation. A new profile-bound review is permitted because there was no valid final judgment; prior outputs remain in the audit history. Runtime configuration changes do not establish or alter scientific merit.
