/**
 * Mobile wrapper that hides its children behind a bottom sheet on small
 * viewports and renders them inline on `lg:` and up. Used by the Use Cases
 * Explorer to collapse its sidebar filter panel.
 */

"use client";

import * as React from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { SlidersHorizontal } from "lucide-react";

export function MobileFiltersSheet({
  children,
  triggerLabel = "Filters",
}: {
  children: React.ReactNode;
  triggerLabel?: string;
}) {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      {/* Desktop: inline children */}
      <div className="hidden lg:block">{children}</div>

      {/* Mobile: trigger button + bottom sheet */}
      <div className="lg:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger
            render={
              <Button variant="outline" size="sm" className="w-full">
                <SlidersHorizontal className="size-3.5" aria-hidden />
                {triggerLabel}
              </Button>
            }
          />
          <SheetContent
            side="bottom"
            className="max-h-[85vh] overflow-y-auto px-4 pb-6 pt-4"
          >
            <SheetHeader className="p-0 pb-3">
              <SheetTitle>{triggerLabel}</SheetTitle>
              <SheetDescription>
                Filters apply instantly as you select them.
              </SheetDescription>
            </SheetHeader>
            {children}
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
