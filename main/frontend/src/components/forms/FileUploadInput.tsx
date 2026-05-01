import { useState } from "react";
import { API_BASE_URL } from "../../api/client";

type UploadResponse = {
  file_path: string;
  filename: string;
  size: number;
};

type Props = {
  label: string;
  onUploaded: (filePath: string) => void;
};

export default function FileUploadInput({ label, onUploaded }: Props) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");

    try {
      const form = new FormData();
      form.append("file", file);
      const resp = await fetch(`${API_BASE_URL}/api/files/upload`, {
        method: "POST",
        body: form,
      });
      const text = await resp.text();
      const data = (text ? JSON.parse(text) : {}) as UploadResponse;
      if (!resp.ok) {
        throw new Error((data as unknown as { detail?: { message?: string } })?.detail?.message ?? "Upload failed.");
      }
      onUploaded(data.file_path);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div style={{ display: "grid", gap: 6 }}>
      <label>{label}</label>
      <input type="file" accept=".csv,.xes" onChange={onChange} disabled={uploading} />
      {uploading && <span>Uploading...</span>}
      {error && <span style={{ color: "crimson" }}>{error}</span>}
    </div>
  );
}

