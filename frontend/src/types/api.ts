/** Request bodies follow frontend/openapi.json. Response bodies are not in that spec. */

export type Meal = "breakfast" | "lunch" | "dinner" | "snack"

export type Sex = "male" | "female"

export type ActivityLevel =
  | "sedentary"
  | "lightly active"
  | "moderately active"
  | "very active"
  | "extra active"

export type NutritionGoal = "maintain" | "lose_weight" | "gain_weight"

export type ActivityType =
  | "walking"
  | "running"
  | "cycling"
  | "swimming"
  | "strength"
  | "yoga"
  | "other_light"
  | "other_moderate"
  | "other_vigorous"

export type HealthCondition = "pregnancy" | "diabetes" | "ibs" | "menstruation"

export type ApiErrorDetail = {
  loc: Array<string | number>
  msg: string
  type: string
}

export type RegisterRequest = {
  name: string
  email: string
  password: string
}

export type UserProfile = {
  id: number
  name: string
  email: string
}

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  access_token: string
  token_type: "Bearer"
}

export type MicronutrientTarget = {
  name: string
  unit: string
  target: number
  direction?: string
  source?: string
  custom?: boolean
}

export type NutritionGoals =
  | { configured: false }
  | {
      configured: true
      age: number
      sex: Sex
      height_cm: number | null
      weight_kg: number | null
      activity_level: ActivityLevel | null
      protein_min: number
      protein_max: number
      carbs: number
      micronutrients: MicronutrientTarget[]
    }

export type NutritionSetupRequest = {
  age: number
  sex: Sex
  height_cm: number
  weight_kg: number
  activity_level: ActivityLevel
  goal: NutritionGoal
}

export type NutritionSetupResponse = {
  bmr: number
  tdee: number
  calories: number
  protein_min: number
  protein_max: number
  carbs: number
  micronutrients: MicronutrientTarget[]
}

export type CalorieGoalResponse = {
  calories: number | null
}

export type CalorieGoalRequest = {
  calories: number
}

export type MacroSplit = {
  configured: boolean
  carbs_percent: number
  protein_percent: number
  fat_percent: number
}

export type MacroSplitRequest = {
  carbs_percent: number
  protein_percent: number
  fat_percent: number
}

export type ConditionGuidance = {
  label: string
  source: string
  summary: string
  nutrients: Record<string, string>
}

export type HealthSettings = {
  conditions: HealthCondition[]
  trimester: 1 | 2 | 3 | null
  custom_calories: number | null
  custom_carbs: number | null
  custom_protein: number | null
  custom_fat: number | null
  micronutrient_overrides: Record<string, number>
  guidance: ConditionGuidance[]
}

export type HealthSettingsRequest = Omit<HealthSettings, "guidance">

export type FoodSummary = {
  /** USDA id; null for a packaged food found only on Open Food Facts (then barcode is set). */
  fdc_id: number | null
  barcode?: string | null
  description: string
  data_type: string
  brand_name: string | null
  gtin_upc: string | null
  /** True when the signed-in user has logged this food before; these come first. */
  previously_logged?: boolean
}

export type FoodSearchResponse = {
  foods: FoodSummary[]
}

export type FoodMeasure = {
  code: string
  label: string
  grams: number
  /** The serving to pre-select, e.g. "1 medium" (household portions come first). */
  default?: boolean
}

export type FoodMeasuresResponse = {
  measures: FoodMeasure[]
}

export type FrequentFood = {
  fdc_id: number | null
  barcode?: string | null
  description: string
  grams: number
  count: number
  last_logged: string
}

export type FrequentFoodsResponse = {
  foods: Record<Meal, FrequentFood[]>
}

export type FoodNutrient = {
  name: string
  unit: string
  per_100g: number
  eaten: number
}

export type FoodLog = {
  id: number
  meal: Meal
  fdc_id: number | null
  barcode?: string | null
  food_name: string
  grams: number
  nutrients: FoodNutrient[]
  logged_at: string
}

export type FoodLogRequest = {
  meal: Meal
  fdc_id?: number | null
  barcode?: string | null
  grams: number
}

export type BarcodeFood = FoodSummary & { source: "USDA" | "Open Food Facts"; kcal_per_100g: number | null }

export type BarcodeResponse = {
  food: BarcodeFood
  measures: FoodMeasure[]
}

export type ApiToken = {
  id: number
  name: string
  timezone: string
  created_at: string
  last_used_at: string | null
}

export type NewApiToken = ApiToken & {
  /** Shown once; only a hash is stored. */
  key: string
}

export type Page<T> = {
  items: T[]
  total: number
  page: number
  per_page: number
}

export type ActivityLogRequest = {
  activity: string
  activity_type: ActivityType
  duration_minutes: number
  weight_kg: number
  height_cm: number
  extra?: boolean
}

export type ActivityLog = {
  id: number
  activity: string
  logged_at: string
  duration_minutes: number | null
  calories_burned: number | null
  activity_type: ActivityType | null
  extra: boolean
}

export type ExerciseSearchResponse = {
  exercises: string[]
}

export type MacroTotal = {
  name: string
  unit: string
  average: number | null
  reported: number
  total_foods: number
  partial: boolean
}

export type MicroAverage = {
  name: string
  unit: string
  average: number | null
  target: number
  limit: boolean
  reported: number
  total_foods: number
  partial: boolean
  status: string
}

export type DailyProgress = {
  name: string
  logged: number | null
  target_label: string
  unit: string
  percent: number | null
  bar_width: number
  partial: boolean
  note: string
}

export type MicronutrientProgress = {
  name: string
  unit: string
  target: number
  limit: boolean
  logged: number | null
  remaining: number | null
  percent: number | null
  bar_width: number
  partial: boolean
}

export type DailyReport = {
  date: string
  timezone: string
  food_log_count: number
  totals: Record<"Calories" | "Protein" | "Carbohydrates" | "Fat", number>
  reported: Record<string, number>
  calorie_goal: number | null
  exercise_credit: number
  progress: DailyProgress[]
  fat_range: [number, number] | null
  custom_macros: Record<string, number | boolean> | null
  protein_min: number | null
  protein_max: number | null
  carbs: number | null
  micronutrients: MicronutrientProgress[]
  condition_nutrition: {
    fiber_logged: number | null
    fiber_goal: number | null
    fiber_percent: number | null
    fiber_partial: boolean
  }
  iron_absorption: IronAbsorptionCheck[]
}

/** One meal with a meaningful amount of iron, and whether it has vitamin C to help absorb it. */
export type IronAbsorptionCheck = {
  meal: "breakfast" | "lunch" | "dinner" | "snack"
  iron_mg: number
  vitamin_c_mg: number | null
  status: "add_vitamin_c" | "good"
  tip: string
  /** True when periods are selected, so the tip is shown more prominently. */
  highlight: boolean
}

export type WeeklyReport = {
  week_start: string
  timezone: string
  logged_days: number
  food_count: number
  macros: MacroTotal[]
  micros: MicroAverage[]
}

export type SavedDaysResponse = {
  days: string[]
}

export type SaveDayResponse = {
  date: string
  saved: boolean
}

export type FoodScore = {
  fdc_id: number
  calories_per_100g: number | null
  score: number | null
  reasons: string[]
  nutrients_per_100kcal: Array<{
    name: string
    unit: string
    amount: number
    percent_of_target: number | null
  }>
}
