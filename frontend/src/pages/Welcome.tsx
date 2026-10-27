import { Link } from "react-router-dom";

import ConsentList from "../components/ConsentList";
import { PageHeader, Panel } from "../components/ui";

export default function Welcome() {
  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        title="Choose what we may use"
        lede="Every switch starts off. Turn on only what you want. You can change these any time on the Privacy page, and you can delete all your data there too."
      />
      <Panel>
        <ConsentList />
      </Panel>
      <div className="mt-6 flex justify-end">
        <Link to="/profile" className="btn-primary">Continue to your profile</Link>
      </div>
    </div>
  );
}
