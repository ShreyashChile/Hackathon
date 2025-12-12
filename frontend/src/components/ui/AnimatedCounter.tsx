"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useSpring, useTransform, useInView } from "framer-motion";

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  className?: string;
  prefix?: string;
  suffix?: string;
  decimals?: number;
}

export function AnimatedCounter({
  value,
  duration = 2,
  className = "",
  prefix = "",
  suffix = "",
  decimals = 0,
}: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const [hasAnimated, setHasAnimated] = useState(false);

  const spring = useSpring(0, {
    duration: duration * 1000,
    bounce: 0,
  });

  const display = useTransform(spring, (current) =>
    current.toFixed(decimals)
  );

  useEffect(() => {
    if (isInView && !hasAnimated) {
      spring.set(value);
      setHasAnimated(true);
    }
  }, [isInView, value, spring, hasAnimated]);

  return (
    <span ref={ref} className={className}>
      {prefix}
      <motion.span>{display}</motion.span>
      {suffix}
    </span>
  );
}

// Large animated number display
interface BigNumberProps {
  value: number;
  label: string;
  prefix?: string;
  suffix?: string;
  color?: "cyan" | "violet" | "rose" | "emerald";
}

const gradientMap = {
  cyan: "from-cyan-400 to-blue-500",
  violet: "from-violet-400 to-purple-500",
  rose: "from-rose-400 to-pink-500",
  emerald: "from-emerald-400 to-green-500",
};

export function BigNumber({
  value,
  label,
  prefix = "",
  suffix = "",
  color = "cyan",
}: BigNumberProps) {
  return (
    <div className="text-center">
      <div
        className={`text-5xl md:text-6xl font-bold bg-gradient-to-r ${gradientMap[color]} bg-clip-text text-transparent`}
      >
        <AnimatedCounter value={value} prefix={prefix} suffix={suffix} />
      </div>
      <p className="text-white/60 mt-2 text-sm font-medium uppercase tracking-wider">
        {label}
      </p>
    </div>
  );
}

