import { initDB, getDB } from './database.ts';

async function testSetup() {
  try {
    console.log('Starting DB Initialization Test...');
    await initDB();
    const db = await getDB();
    
    // Check if the tables exist
    const tables = await db.all("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'");
    console.log('Tables found in database:', tables.map(t => t.name).join(', '));
    
    if (tables.length === 5) {
      console.log('Success! All 5 tables were created perfectly in SQLite.');
    } else {
      console.error(`Warning: Expected 5 tables but found ${tables.length}.`);
    }
  } catch (error) {
    console.error('Error initializing database:', error);
    process.exit(1);
  }
}

testSetup();
