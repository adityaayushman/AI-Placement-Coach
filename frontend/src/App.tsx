import { Suspense, lazy, type ReactNode } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import Shell from "./components/Shell";
import { Loading } from "./components/ui";
import AuthPage from "./pages/AuthPage";

const Admin = lazy(() => import("./pages/Admin"));
const Coordinator = lazy(() => import("./pages/Coordinator"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Interview = lazy(() => import("./pages/Interview"));
const Practice = lazy(() => import("./pages/Practice"));
const Privacy = lazy(() => import("./pages/Privacy"));
const Profile = lazy(() => import("./pages/Profile"));
const Resume = lazy(() => import("./pages/Resume"));
const Welcome = lazy(() => import("./pages/Welcome"));

const HOME = { student: "/", coordinator: "/coordinator", admin: "/admin" } as const;

function Guard({ roles, children }: { roles: (keyof typeof HOME)[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center"><Loading /></div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to={HOME[user.role]} replace />;
  return <Suspense fallback={<Loading />}>{children}</Suspense>;
}

function Public({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user ? <Navigate to={HOME[user.role]} replace /> : <>{children}</>;
}

function NotFound() {
  return (
    <div className="glass mx-auto mt-24 max-w-md p-8 text-center">
      <h1 className="font-serif text-3xl">Page not found</h1>
      <p className="mt-3 text-muted">That page does not exist. <Link to="/" className="text-amber hover:underline">Go to your overview</Link></p>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Public><AuthPage mode="login" /></Public>} />
      <Route path="/register" element={<Public><AuthPage mode="register" /></Public>} />
      <Route element={<Guard roles={["student", "coordinator", "admin"]}><Shell /></Guard>}>
        <Route path="/" element={<Guard roles={["student"]}><Dashboard /></Guard>} />
        <Route path="/welcome" element={<Guard roles={["student"]}><Welcome /></Guard>} />
        <Route path="/profile" element={<Guard roles={["student"]}><Profile /></Guard>} />
        <Route path="/resume" element={<Guard roles={["student"]}><Resume /></Guard>} />
        <Route path="/practice" element={<Guard roles={["student"]}><Practice /></Guard>} />
        <Route path="/interview" element={<Guard roles={["student"]}><Interview /></Guard>} />
        <Route path="/privacy" element={<Guard roles={["student"]}><Privacy /></Guard>} />
        <Route path="/coordinator" element={<Guard roles={["coordinator", "admin"]}><Coordinator /></Guard>} />
        <Route path="/admin" element={<Guard roles={["admin"]}><Admin /></Guard>} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
