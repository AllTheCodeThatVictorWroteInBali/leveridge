export default function PdfInput({ disabled, onChange }) {
	return (
		<>
			<label htmlFor="pdf">PDF file</label>
			<input
				id="pdf"
				name="file"
				type="file"
				accept=".pdf,application/pdf"
				required
				disabled={disabled}
				onChange={onChange}
			/>
		</>
	);
}
