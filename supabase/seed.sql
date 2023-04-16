-- AGENTS TABLE
-- Agent 1
INSERT INTO public."Agents" (full_name, bio, directives, pending_plans)
VALUES ('John Doe', 'AI researcher and developer', ARRAY['Improve AI models', 'Design new algorithms'], ARRAY[1, 2]::bigint[]);

-- Agent 2
INSERT INTO public."Agents" (full_name, bio, directives, pending_plans)
VALUES ('Jane Smith', 'Robotics engineer', ARRAY['Develop new robotic applications', 'Refine motion control'], ARRAY[3, 4]::bigint[]);

-- MEMORIES TABLE
-- Memory 1 - John
INSERT INTO public."Memories" (agent_id, type, description, related_memories, embedding, importance, last_accessed, related_agent_ids)
VALUES (1, 'experience', 'John Doe Attended AI conference last month with Jane Smith', ARRAY[2]::bigint[], NULL, 0.75, NOW(), ARRAY[1, 2]);

-- Memory 2 - John
INSERT INTO public."Memories" (agent_id, type, description, related_memories, embedding, importance, last_accessed, related_agent_ids)
VALUES (1, 'experience', 'John Doe Read a new paper on reinforcement learning', ARRAY[]::bigint[], NULL, 0.65, NOW(), ARRAY[1]);

-- Memory 3 - John
INSERT INTO public."Memories" (agent_id, type, description, related_memories, embedding, importance, last_accessed, related_agent_ids)
VALUES (1, 'reflection', 'Jane Smith has an interest in AI', ARRAY[1]::bigint[], NULL, 0.65, NOW(), ARRAY[2]);

-- Memory 4 - Jane
INSERT INTO public."Memories" (agent_id, type, description, related_memories, embedding, importance, last_accessed, related_agent_ids)
VALUES (2, 'experience', 'Jane Smith Built a new robot prototype', ARRAY[]::bigint[], NULL, 0.9, NOW(), ARRAY[2]);

-- Memory 5 - Jane
INSERT INTO public."Memories" (agent_id, type, description, related_memories, embedding, importance, last_accessed, related_agent_ids)
VALUES (2, 'experience', 'Jane Smith Attended AI conference last month with John Doe', ARRAY[]::bigint[], NULL, 0.75, NOW(), ARRAY[1, 2]);

-- Memory 6 - Jane
INSERT INTO public."Memories" (agent_id, type, description, related_memories, embedding, importance, last_accessed, related_agent_ids)
VALUES (2, 'reflection', 'John Doe is a dedicated researcher', ARRAY[5]::bigint[], NULL, 0.65, NOW(), ARRAY[1]);

-- Memory 7 - Jane
INSERT INTO public."Memories" (agent_id, type, description, related_memories, embedding, importance, last_accessed, related_agent_ids)
VALUES (2, 'observation', 'John Doe told me about his upcoming presentation', ARRAY[]::bigint[], NULL, 0.45, NOW(), ARRAY[1]);

-- PLANS TABLE
-- Plan 1 - John
INSERT INTO public."Plans" (agent_id, description, max_duration_hrs, stop_condition, completed_at)
VALUES (1, 'Implement a new AI model for decision-making', 40, 'Model achieves 95% accuracy', NULL);

-- Plan 2 - John
INSERT INTO public."Plans" (agent_id, description, max_duration_hrs, stop_condition, completed_at)
VALUES (1, 'Refactor AI codebase for modularity', 20, 'All code is refactored and tested', NOW());

-- Plan 3 - Jane
INSERT INTO public."Plans" (agent_id, description, max_duration_hrs, stop_condition, completed_at)
VALUES (2, 'Test new robotic arm motion control', 10, 'Arm moves smoothly and accurately', NULL);

-- Plan 4 - Jane
INSERT INTO public."Plans" (agent_id, description, max_duration_hrs, stop_condition, completed_at)
VALUES (2, 'Implement haptic feedback into robot arms', 30, 'Arm accurately senses haptic signals', NULL);

