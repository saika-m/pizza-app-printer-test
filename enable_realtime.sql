-- Run this in your Supabase Dashboard -> SQL Editor
-- This enables Realtime updates for the 'orders' table
alter publication supabase_realtime add table orders;

-- Verify it worked by running:
-- select * from pg_publication_tables where pubname = 'supabase_realtime';
