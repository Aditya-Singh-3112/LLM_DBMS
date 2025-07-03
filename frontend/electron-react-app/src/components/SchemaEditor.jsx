// File: src/components/SchemaEditor.jsx
import { useState, useEffect } from "react";
import axios from "axios";

export default function SchemaEditor({ collection, onBack }) {
  const [columns, setColumns] = useState([]);

  useEffect(() => {
    if (!collection) return;

    axios.get(`http://localhost:8000/schema/${collection}`)
      .then(res => {
        const props = res.data.properties || {};
        const loadedColumns = Object.entries(props).map(([key, val]) => ({
          name: key,
          type: val.type || "string"
        }));
        setColumns(loadedColumns);
      })
      .catch(() => setColumns([]));
  }, [collection]);

  const addColumn = () => {
    setColumns([...columns, { name: "", type: "string" }]);
  };

  const updateColumn = (idx, field, value) => {
    const updated = [...columns];
    updated[idx][field] = value;
    setColumns(updated);
  };

  const saveSchema = async () => {
    const schema = {
      $schema: "http://json-schema.org/draft-07/schema#",
      title: collection,
      type: "object",
      properties: {},
      required: [],
    };
    for (const col of columns) {
      if (!col.name.trim()) continue;
      schema.properties[col.name] = { type: col.type };
    }
    await axios.post(`http://localhost:8000/schema/${collection}`, { schema });
    alert("Schema saved!");
    onBack();
  };

  return (
    <div className="p-4 overflow-auto">
      <h2 className="text-xl mb-4">Edit Schema: {collection}</h2>
      <button
        onClick={onBack}
        className="mb-4 px-3 py-1 bg-gray-300 rounded hover:bg-gray-400"
      >
        ← Back
      </button>

      <table className="w-full mb-4">
        <thead>
          <tr className="border-b">
            <th className="text-left py-2">Column Name</th>
            <th className="text-left py-2">Type</th>
          </tr>
        </thead>
        <tbody>
          {columns.map((col, idx) => (
            <tr key={idx}>
              <td>
                <input
                  className="p-1 border rounded w-full"
                  value={col.name}
                  onChange={(e) => updateColumn(idx, "name", e.target.value)}
                />
              </td>
              <td>
                <select
                  className="p-1 border rounded"
                  value={col.type}
                  onChange={(e) => updateColumn(idx, "type", e.target.value)}
                >
                  <option value="string">string</option>
                  <option value="number">number</option>
                  <option value="boolean">boolean</option>
                  <option value="array">array</option>
                  <option value="object">object</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <button
        onClick={addColumn}
        className="mr-2 px-3 py-1 bg-blue-500 text-white rounded"
      >
        + Add Column
      </button>
      <button
        onClick={saveSchema}
        className="px-3 py-1 bg-green-600 text-white rounded"
      >
        💾 Save Schema
      </button>
    </div>
  );
}
