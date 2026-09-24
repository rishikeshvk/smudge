import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { readClockOptions } from "./api/@tanstack/react-query.gen";

const TICK_MS = 60_000;

// How far the Kindred Clock runs from this phone's clock, measured when it was last read.
export function clockOffset(kindredNow: string, readAt: number): number {
  return Date.parse(kindredNow) - readAt;
}

// The Kindred Clock in dev builds, so fast-forwarding moves the app too; real time otherwise
// (the endpoint answers 404 outside dev mode).
export function useKindredNow(): Date {
  const clock = useQuery({ ...readClockOptions(), retry: false });
  const [phoneNow, setPhoneNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => setPhoneNow(Date.now()), TICK_MS);
    return () => clearInterval(timer);
  }, []);

  const offset = clock.data ? clockOffset(clock.data.now, clock.dataUpdatedAt) : 0;
  return new Date(phoneNow + offset);
}
