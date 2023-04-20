-- WORLDS TABLE
INSERT INTO public."Worlds" (id, name, current_step)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'AI Discord Server', 0);

-- LOCATIONS TABLE
INSERT INTO public."Locations" (id, world_id, name, description, channel_id, allowed_agent_ids)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'water-cooler', 'A place to chit chat', 8395726143, ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12']::uuid[]);

INSERT INTO public."Locations" (id, world_id, name, description, channel_id, allowed_agent_ids)
VALUES ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'quiet-area', 'A place to do focused work', 8395726144, ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12']::uuid[]);

INSERT INTO public."Locations" (id, world_id, name, description, channel_id, allowed_agent_ids)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'outside', 'A place to get some fresh air', 8395726145, ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12']::uuid[]);

-- AGENTS TABLE
INSERT INTO public."Agents" (id, full_name, bio, directives, ordered_plan_ids, world_id, location_id)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'John Doe', 'John is an AI researcher and developer', ARRAY['Improve AI models'], ARRAY['a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13']::uuid[], 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13',  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14');

INSERT INTO public."Agents" (id, full_name, bio, directives, ordered_plan_ids, world_id, location_id)
VALUES ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Jane Smith', 'Jane is a Robotics engineer. She is currently getting her PHD at the University of California, Los Angeles. She loves riding her bike on the weekends, and has a secret passion for horseback riding.', ARRAY['Develop new robotic applications'], ARRAY['b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14']::uuid[], 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15');

-- PLANS TABLE
INSERT INTO public."Plans" (id, agent_id, description, max_duration_hrs, stop_condition, location_id)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Research new semantic embedding algorithms', 2, 'Research is complete', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15');

INSERT INTO public."Plans" (id, agent_id, description, max_duration_hrs, stop_condition, location_id)
VALUES ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Write a paper on advanced robotics', 2, 'Paper is written', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15');

