
### To set up a local supabase instance
`supabase login` 
`supabase init`
`supabase start`

Then replace the SUPABASE_DEV_URL and SUPABASE_DEV_KEY in the .ev file with the values you are given

`supabase db reset`

This will use the migration file in supabase/migrations/initial_schema to set up the tables and columns
This will also seed the db with two dummy agents, as specified in supabase/seed.sql

### To run the src/testing.py file:
`poetry run test`


### Next steps
I have implemented a simple planning process
Now the agents need tools. I haven't done that