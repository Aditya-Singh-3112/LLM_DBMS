export default function ResultViewer({ data }) {
  if (!data || data.status === undefined) {
    return <div className="p-4 text-gray-600">No query run yet.</div>;
  }

  if (data.status === "error") {
    return <div className="p-4 text-red-600">Error: {data.error}</div>;
  }

  if (data.results) {
    return (
      <pre className="p-4 overflow-auto bg-gray-100 rounded">
        {JSON.stringify(data.results, null, 2)}
      </pre>
    );
  }

  if (data.id) {
    return <div className="p-4">Inserted document with ID: {data.id}</div>;
  }

  if (data.deleted !== undefined) {
    return <div className="p-4">Deleted {data.deleted} document(s)</div>;
  }

  return <div className="p-4">Unknown response.</div>;
}
