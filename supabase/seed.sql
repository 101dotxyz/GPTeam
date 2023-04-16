-- AGENTS TABLE
-- Agent 1
INSERT INTO public."Agents" (id, full_name, bio, directives)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'John Doe', 'AI researcher and developer', ARRAY['Improve AI models', 'Design new algorithms']);

-- Agent 2
INSERT INTO public."Agents" (id, full_name, bio, directives)
VALUES ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Jane Smith', 'Robotics engineer', ARRAY['Develop new robotic applications', 'Refine motion control']);

-- MEMORIES TABLE
-- Memory 1 - John
INSERT INTO public."Memories" (id, agent_id, type, description, related_memory_ids, embedding, importance, last_accessed, related_agent_ids)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'observation', 'John Doe Attended AI conference last month with Jane Smith', ARRAY['c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14']::uuid[], NULL, 3, NOW(), ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12']::uuid[]);

-- Memory 2 - John
INSERT INTO public."Memories" (id, agent_id, type, description, related_memory_ids, embedding, importance, last_accessed, related_agent_ids)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'observation', 'John Doe Read a new paper on reinforcement learning', ARRAY[]::uuid[], NULL, 1, NOW(), ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11']::uuid[]);

-- Memory 3 - John
INSERT INTO public."Memories" (id, agent_id, type, description, related_memory_ids, embedding, importance, last_accessed, related_agent_ids)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'reflection', 'Jane Smith has an interest in AI', ARRAY['c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13']::uuid[], NULL, 2, NOW(), ARRAY['b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12']::uuid[]);

-- Memory 4 - Jane
INSERT INTO public."Memories" (id, agent_id, type, description, related_memory_ids, embedding, importance, last_accessed, related_agent_ids)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'observation', 'Jane Smith Built a new robot prototype', ARRAY[]::uuid[], NULL, 6, NOW(), ARRAY['b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12']::uuid[]);

-- Memory 5 - Jane
INSERT INTO public."Memories" (id, agent_id, type, description, related_memory_ids, embedding, importance, last_accessed, related_agent_ids)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'observation', 'Jane Smith Attended AI conference last month with John Doe', ARRAY[]::uuid[], NULL, 2, NOW(), ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12']::uuid[]);

-- Memory 6 - Jane
INSERT INTO public."Memories" (id, agent_id, type, description, related_memory_ids, embedding, importance, last_accessed, related_agent_ids)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'reflection', 'John Doe is a dedicated researcher', ARRAY['c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a17']::uuid[], NULL, 3, NOW(), ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11']::uuid[]);

-- Memory 7 - Jane
INSERT INTO public."Memories" (id, agent_id, type, description, related_memory_ids, embedding, importance, last_accessed, related_agent_ids)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a19', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'observation', 'John Doe told me about his upcoming presentation', ARRAY[]::uuid[], NULL, 2, NOW(), ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11']::uuid[]);

-- PLANS TABLE
-- Plan 1 - John
INSERT INTO public."Plans" (id, agent_id, description, max_duration_hrs, stop_condition, completed_at)
VALUES ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a20', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Implement a new AI model for decision-making', 40, 'Model achieves 95% accuracy', NULL);

-- Plan 2 - John
INSERT INTO public."Plans" (id, agent_id, description, max_duration_hrs, stop_condition, completed_at)
VALUES ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Refactor AI codebase for modularity', 20, 'All code is refactored and tested', NOW());

-- Plan 3 - Jane
INSERT INTO public."Plans" (id, agent_id, description, max_duration_hrs, stop_condition, completed_at)
VALUES ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Test new robotic arm motion control', 10, 'Arm moves smoothly and accurately', NULL);

-- Plan 4 - Jane
INSERT INTO public."Plans" (id, agent_id, description, max_duration_hrs, stop_condition, completed_at)
VALUES ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a23', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Implement haptic feedback into robot arms', 30, 'Arm accurately senses haptic signals', NULL);

-- Update Agents with ordered_plan_ids
UPDATE public."Agents" SET ordered_plan_ids = ARRAY['d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a20', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21']::uuid[] WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
UPDATE public."Agents" SET ordered_plan_ids = ARRAY['d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a23']::uuid[] WHERE id = 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12';
