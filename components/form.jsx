import { useState } from "react";
import PdfInput from "./input.jsx";

export default function UploadForm() {
	const [file, setFile] = useState(null);
	const [loading, setLoading] = useState(false);
	const [result, setResult] = useState("No file uploaded.");

	async function handleRead(event) {
		event.preventDefault();
		if (!file || loading) return;
		if (!file.name.toLowerCase().endsWith(".pdf")) {
			setResult("Please upload a PDF file.");
			return;
		}
		setLoading(true);
		setResult("Uploading...");
		try {
			const formData = new FormData();
			formData.append("file", file);
			const response = await fetch("/read", { method: "POST", body: formData });
			if (!response.ok) throw new Error(`Request failed (${response.status})`);
			const data = await response.json();
			console.log(data);
			setResult(JSON.stringify(data, null, 2));
		} catch (error) {
			setResult(error.message);
		} finally {
			setLoading(false);
		}
	}

	return (
		<>
			<form onSubmit={handleRead}>
				<PdfInput
					disabled={loading}
					onChange={event => {
						setFile(event.target.files[0] ?? null);
						setResult("No file uploaded.");
					}}
				/>
				<button type="submit" disabled={loading || !file}>
					<span aria-hidden="true">{"\u2191"}</span> Upload
				</button>
			</form>
			<pre id="result" role="status" aria-live="polite">{result}</pre>
		</>
	);
}
