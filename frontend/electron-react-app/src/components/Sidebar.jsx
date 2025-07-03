import { useEffect, useState } from "react";
import axios from "axios";

export default function Sidebar({ onSelect, onEditSchema, editing }) {
  const [items, setItems] = useState([]);

  const fetchItems = () => {
    const url = editing
      ? "http://localhost:8000/schema"         // GET /schema for schemas
      : "http://localhost:8000/collections";   // GET /collections for data

    axios.get(url)
      .then(res => {
        setItems(res.data);
      })
      .catch(err => {
        console.error("Failed to fetch items:", err);
      });
  };

  useEffect(() => {
    fetchItems();
  }, [editing]);

  const createSchema = async () => {
    const name = window.prompt("Enter new schema (collection) name:");
    if (!name) return;

    try {
      const defaultSchema = {
        $schema: "http://json-schema.org/draft-07/schema#",
        title: name,
        type: "object",
        properties: {},
        required: [],
      };

      // ✅ Correct POST route to match FastAPI backend
      await axios.post(`http://localhost:8000/schemas/${name}`, {
        schema: defaultSchema,
      });

      fetchItems(); // Refresh sidebar after saving
    } catch (err) {
      console.error("Failed to create schema:", err);
    }
  };

  return (
    <aside className="w-60 p-4 border-r h-full flex flex-col">
      <h2 className="text-xl mb-4">
        {editing ? "Schemas" : "Collections"}
      </h2>

      <button
        onClick={() => onEditSchema(!editing)}
        className="mb-4 px-2 py-1 text-sm bg-yellow-400 rounded"
      >
        {editing ? "Back to Queries" : "Edit Schemas"}
      </button>

      {editing && (
        <button
          onClick={createSchema}
          className="mb-2 px-2 py-1 text-sm bg-green-500 text-white rounded"
        >
          + New Schema
        </button>
      )}

      <ul className="flex-grow overflow-auto">
        {items.map(item => (
          <li key={item}>
            <button
              onClick={() => onSelect(item)}
              className="w-full text-left py-1 hover:bg-gray-200 rounded"
            >
              {item}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
