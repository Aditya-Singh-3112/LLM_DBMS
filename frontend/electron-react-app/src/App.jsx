import { useState } from "react";
import Sidebar from "./components/Sidebar";
import PromptInput from "./components/PromptInput";
import ResultViewer from "./components/ResultViewer";
import SchemaEditor from "./components/SchemaEditor";

export default function App() {
  const [selectedItem, setSelectedItem] = useState(null);
  const [queryResult, setQueryResult] = useState({});
  const [editingSchema, setEditingSchema] = useState(false);

  const handleSelect = (item) => {
    setSelectedItem(item);
    setQueryResult({});
  };

  const handleBackFromEditor = () => {
    setSelectedItem(null);
  };

  return (
    <div className="flex h-screen">
      <Sidebar
        onSelect={handleSelect}
        onEditSchema={setEditingSchema}
        editing={editingSchema}
      />

      <div className="flex-1 flex flex-col">
        {editingSchema ? (
          selectedItem ? (
            <SchemaEditor
              collection={selectedItem}
              onBack={handleBackFromEditor}
            />
          ) : (
            <div className="p-4 text-gray-600">Select or create a schema to view.</div>
          )
        ) : (
          <>
            <PromptInput onResults={setQueryResult} />
            <div className="p-4 flex-grow overflow-auto">
              <ResultViewer data={queryResult} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
