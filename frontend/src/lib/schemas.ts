import { z } from "zod"
import type { HealthCondition } from "../types/api.ts"

const activityLevels = ["sedentary", "lightly active", "moderately active", "very active", "extra active"] as const
const goals = ["maintain", "lose_weight", "gain_weight"] as const
const conditions = ["pregnancy", "diabetes", "ibs", "menstruation"] as const

function rangedNumber(min: number, max: number, emptyMessage: string, rangeMessage: string, integer = false) {
  return z.string().trim().superRefine((value, context) => {
    if (!value) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: emptyMessage })
      return
    }
    const number = Number(value)
    const invalid = !Number.isFinite(number)
      || (integer && !Number.isInteger(number))
      || number < min
      || number > max
    if (invalid) context.addIssue({ code: z.ZodIssueCode.custom, message: rangeMessage })
  })
}

function optionalAmount(min: number, max: number, message: string, exclusiveMin = false) {
  return z.string().trim().superRefine((value, context) => {
    if (!value) return
    const number = Number(value)
    const below = exclusiveMin ? number <= min : number < min
    if (!Number.isFinite(number) || below || number > max) {
      context.addIssue({ code: z.ZodIssueCode.custom, message })
    }
  })
}

export function readNumber(value: string): number {
  return Number(value)
}

export function readOptionalNumber(value: string): number | null {
  return value.trim() ? Number(value) : null
}

export const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email."),
  password: z.string().min(1, "Enter your password.").max(128, "Password must be at most 128 characters."),
})

export const registerSchema = z.object({
  name: z.string().trim().min(1, "Enter your name.").max(100, "Name must be at most 100 characters."),
  email: z.string().trim().email("Enter a valid email."),
  password: z
    .string()
    .min(8, "Use at least 8 characters.")
    .max(128, "Password must be at most 128 characters.")
    .refine((value) => new TextEncoder().encode(value).length <= 72, "Password must be at most 72 UTF-8 bytes."),
})

export type LoginValues = z.infer<typeof loginSchema>
export type RegisterValues = z.infer<typeof registerSchema>

export const nutritionSchema = z.object({
  age: rangedNumber(18, 100, "Enter your age.", "Age must be a whole number from 18 to 100.", true),
  sex: z.enum(["male", "female"]),
  height_cm: rangedNumber(50, 300, "Enter your height.", "Height must be from 50 to 300 cm."),
  weight_kg: rangedNumber(20, 500, "Enter your weight.", "Weight must be from 20 to 500 kg."),
  activity_level: z.enum(activityLevels),
  goal: z.enum(goals),
})

export type NutritionInput = z.infer<typeof nutritionSchema>

export const calorieSchema = z.object({
  calories: rangedNumber(500, 10000, "Enter a calorie target.", "Calories must be from 500 to 10,000."),
})

export const healthSchema = z.object({
  conditions: z.array(z.enum(conditions)),
  trimester: z.enum(["", "1", "2", "3"]),
  custom_calories: optionalAmount(500, 10000, "Care-plan calories must be from 500 to 10,000."),
  custom_carbs: optionalAmount(0, 1500, "Carbohydrates must be greater than 0 and at most 1,500 g.", true),
  custom_protein: optionalAmount(0, 1500, "Protein must be greater than 0 and at most 1,500 g.", true),
  custom_fat: optionalAmount(0, 1500, "Fat must be greater than 0 and at most 1,500 g.", true),
}).superRefine((value, context) => {
  const selected = new Set<HealthCondition>(value.conditions)
  if (selected.has("pregnancy") && selected.has("menstruation")) {
    context.addIssue({ code: z.ZodIssueCode.custom, path: ["conditions"], message: "Choose pregnancy or periods, not both." })
  }
  if (selected.has("pregnancy") && value.trimester === "") {
    context.addIssue({ code: z.ZodIssueCode.custom, path: ["trimester"], message: "Choose a pregnancy trimester." })
  }
})

export type HealthInput = z.infer<typeof healthSchema>
export type CalorieInput = z.infer<typeof calorieSchema>
