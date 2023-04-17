CREATE extension if not exists "pgcrypto" with schema "extensions";
create extension if not exists "vector" with schema "extensions";

create type "public"."memory_type" as enum ('reflection', 'observation');

create table "public"."Agents" (
    "id" uuid DEFAULT uuid_generate_v4() not null,
    "full_name" text,
    "bio" text,
    "directives" text[],
    "ordered_plan_ids" uuid[]
);

create table "public"."Memories" (
    "id" uuid DEFAULT uuid_generate_v4() not null,
    "created_at" timestamp with time zone default now(),
    "agent_id" uuid,
    "type" memory_type,
    "description" text,
    "related_memory_ids" uuid[],
    "embedding" vector(1536),
    "importance" smallint,
    "last_accessed" timestamp with time zone,
    "related_agent_ids" uuid[]
);

create table "public"."Plans" (
    "id" uuid DEFAULT uuid_generate_v4() not null,
    "created_at" timestamp with time zone default now(),
    "agent_id" uuid,
    "description" text,
    "max_duration_hrs" real,
    "stop_condition" text,
    "completed_at" timestamp with time zone
);

CREATE UNIQUE INDEX "Agents_pkey" ON public."Agents" USING btree (id);

CREATE UNIQUE INDEX "Memories_pkey" ON public."Memories" USING btree (id);

CREATE UNIQUE INDEX "Plans_pkey" ON public."Plans" USING btree (id);

alter table "public"."Agents" add constraint "Agents_pkey" PRIMARY KEY using index "Agents_pkey";

alter table "public"."Memories" add constraint "Memories_pkey" PRIMARY KEY using index "Memories_pkey";

alter table "public"."Plans" add constraint "Plans_pkey" PRIMARY KEY using index "Plans_pkey";
