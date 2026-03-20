import { Suspense } from "react";

import AnalyticsClient from "./analytics-client";

export const dynamic = "force-dynamic";

export default function AnalyticsPage() {
  return (
    <Suspense fallback={null}>
      <AnalyticsClient />
    </Suspense>
  );
}
