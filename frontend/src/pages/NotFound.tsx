import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <>
      <h1 className="font-serif text-3xl">Page not found</h1>
      <p className="mt-4 text-muted">
        That page doesn't exist. <Link to="/" className="text-accent underline">Back to overview</Link>
      </p>
    </>
  );
}
