from flask import Flask, render_template, request
import pandas as pd
from scipy.optimize import linprog

app = Flask(__name__)

# Load meal data from CSV
df = pd.read_csv('Meal-Plan-Optimized-Source.csv')


def calculate_meals(meal_quantities, calorie_limit, protein_min, protein_max, carb_min, carb_max, fat_min, fat_max):
    # Maximizes tastiness, with tastiness values assigned to each food
    original_list = df['Tastiness Index'].tolist()
    obj = [-x for x in original_list]

    lhs_ineq = [df['Total Calories'].tolist(),  # Calorie limit constraint defined at beginning of program
                df['Fat (g)'].tolist(),  # Fat max value
                [-x for x in df['Fat (g)'].tolist()],  # Fat min value
                df['Carbs (g)'].tolist(),  # Carb max value
                [-x for x in df['Carbs (g)'].tolist()],  # Carb min value
                df['Protein (g)'].tolist(),  # Protein max value
                [-x for x in df['Protein (g)'].tolist()]]  # Protein min value

    # Upper limit constraints for servings (each meal serving <= 3)
    for i in range(len(df)):
        constraint = [0] * len(df)
        constraint[i] = 1
        lhs_ineq.append(constraint)

    # Lower limit constraints for servings (each meal serving >= 0)
    for i in range(len(df)):
        constraint = [0] * len(df)
        constraint[i] = -1
        lhs_ineq.append(constraint)

    # Calculate already consumed nutrients
    pre_calories = 0
    pre_fat = 0
    pre_carb = 0
    pre_protein = 0

    for index, row in df.iterrows():
        servings = meal_quantities.get(f'meal_{index}', 0)
        pre_calories += row['Total Calories'] * servings
        pre_fat += row['Fat (g)'] * servings
        pre_carb += row['Carbs (g)'] * servings
        pre_protein += row['Protein (g)'] * servings

    rhs_ineq = [calorie_limit - pre_calories,  # Calorie limit constraint adjusted for consumed calories
                fat_max - pre_fat,  # Fat max value adjusted for consumed fat
                -fat_min + pre_fat,  # Fat min value adjusted for consumed fat
                carb_max - pre_carb,  # Carb max value adjusted for consumed carbs
                -carb_min + pre_carb,  # Carb min value adjusted for consumed carbs
                protein_max - pre_protein,  # Protein max value adjusted for consumed protein
                -protein_min + pre_protein]  # Protein min value adjusted for consumed protein

    # Upper limit value for servings
    for _ in range(len(df)):
        rhs_ineq.append(3)

    # Lower limit value for servings (0 because we want non-negative servings)
    for _ in range(len(df)):
        rhs_ineq.append(0)

    opt = linprog(c=obj, A_ub=lhs_ineq, b_ub=rhs_ineq, method="highs")

    list_output = opt.x

    result = []
    total_calories = pre_calories
    total_protein = pre_protein
    total_fat = pre_fat
    total_carbs = pre_carb

    for i in range(len(list_output)):
        if list_output[i] == 0.:
            continue
        else:
            servings = list_output[i]
            result.append(f"{df['Name'].iloc[i]}: {servings}")
            total_calories += df['Total Calories'].iloc[i] * servings
            total_protein += df['Protein (g)'].iloc[i] * servings
            total_fat += df['Fat (g)'].iloc[i] * servings
            total_carbs += df['Carbs (g)'].iloc[i] * servings

    result.append(f"Total Calories: {total_calories}")
    result.append(f"Total Protein: {total_protein} g")
    result.append(f"Total Fat: {total_fat} g")
    result.append(f"Total Carbohydrates: {total_carbs} g")

    return result


@app.route('/')
def index():
    return render_template('index.html', df=df)


@app.route('/calculate', methods=['POST'])
def calculate():
    meal_quantities = {}
    for index, row in df.iterrows():
        meal_quantities[f'meal_{index}'] = float(request.form.get(f'meal_{index}', 0))

    calorie_limit = float(request.form['calorie_limit'])
    protein_min = float(request.form['protein_min'])
    protein_max = float(request.form['protein_max'])
    carb_min = float(request.form['carb_min'])
    carb_max = float(request.form['carb_max'])
    fat_min = float(request.form['fat_min'])
    fat_max = float(request.form['fat_max'])

    calculated_meals = calculate_meals(meal_quantities, calorie_limit, protein_min, protein_max, carb_min, carb_max,
                                       fat_min, fat_max)

    return render_template('result.html', calculated_meals=calculated_meals)


if __name__ == '__main__':
    app.run(debug=True)
