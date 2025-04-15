from flask import Flask, request, jsonify

# new comment...
app = Flask(__name__)
notes = {}

@app.route('/notes', methods=['POST'])
def create_note():
    data = request.json
    note_id = str(len(notes) + 1)
    notes[note_id] = data['content']
    return jsonify({'id': note_id, 'content': notes[note_id]}), 201

@app.route('/notes', methods=['GET'])
def list_notes():
    return jsonify([{'id': note_id, 'content': content} for note_id, content in notes.items()])

@app.route('/notes/<note_id>', methods=['GET'])
def read_note(note_id):
    if note_id not in notes:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify({'id': note_id, 'content': notes[note_id]})

@app.route('/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    if note_id not in notes:
        return jsonify({'error': 'Note not found'}), 404
    notes[note_id] = request.json['content']
    return jsonify({'id': note_id, 'content': notes[note_id]})

@app.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    if note_id not in notes:
        return jsonify({'error': 'Note not found'}), 404
    del notes[note_id]
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
