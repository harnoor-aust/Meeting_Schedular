from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

# Initialize the database and create tables if they do not exist
def init_db():
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            organizer TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room_id INTEGER NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    ''')
    conn.commit()
    cursor.execute("INSERT OR IGNORE INTO rooms (name) VALUES ('Zoloto'), ('Aurum'), ('Kin'), ('Break Room')")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms")
    rooms = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    conn.close()
    return render_template('index.html', rooms=rooms)

@app.route('/events', methods=['GET'])
def get_events():
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT events.id, events.title, events.organizer, events.start_time, events.end_time, rooms.name AS room_name
        FROM events
        JOIN rooms ON events.room_id = rooms.id
    ''')
    events = [
        {
            'id': row[0],
            'title': row[1],
            'organizer': row[2],
            'start_time': row[3],
            'end_time': row[4],
            'room_name': row[5]
        } for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(events)

@app.route('/add_event', methods=['POST'])
def add_event():
    data = request.json
    title = data.get('title')
    organizer = data.get('organizer')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    room_id = data.get('room')

    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM events
        WHERE room_id = ? AND (
            (start_time < ? AND end_time > ?) OR
            (start_time < ? AND end_time > ?) OR
            (start_time >= ? AND end_time <= ?)
        )
    ''', (room_id, end_time, start_time, start_time, end_time, start_time, end_time))

    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Room is already booked for this time'}), 400

    cursor.execute('''
        INSERT INTO events (title, organizer, start_time, end_time, room_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, organizer, start_time, end_time, room_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Meeting added successfully'})

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    
    if not event:
        conn.close()
        return jsonify({'message': 'Event not found'}), 404

    cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Meeting canceled successfully'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
