import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

export default function PageTransition({ children }) {
  const location = useLocation();
  const [displayChildren, setDisplayChildren] = useState(children);
  const [transitionStage, setTransitionStage] = useState("enter");
  const prevPath = useRef(location.pathname);

  useEffect(() => {
    if (location.pathname !== prevPath.current) {
      setTransitionStage("exit");
      prevPath.current = location.pathname;
    }
  }, [location.pathname]);

  useEffect(() => {
    if (transitionStage === "exit") {
      const timeout = setTimeout(() => {
        setDisplayChildren(children);
        setTransitionStage("enter");
      }, 200);
      return () => clearTimeout(timeout);
    }
  }, [transitionStage, children]);

  useEffect(() => {
    if (transitionStage !== "exit") {
      setDisplayChildren(children);
    }
  }, [children, transitionStage]);

  return (
    <div
      className={`page-transition ${transitionStage === "exit" ? "page-exit" : "page-enter"}`}
    >
      {displayChildren}
    </div>
  );
}
