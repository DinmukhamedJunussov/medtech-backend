import OpenAI from 'openai';
import { LlamaParseReader } from 'llamaindex';
import * as fs from 'fs';

// Constants from const.py
const nazvaniya_analizov = [
    "Гемоглобин",
    "Эритроциты",
    "MCV",
    "RDW",
    "MCH",
    "MCHC",
    "Гематокрит",
    "Тромбоциты",
    "Лейкоциты",
    "СОЭ",
    "Нейтрофилы %",
    "Палочкоядерные нейтрофилы",
    "Сегментоядерные нейтрофилы",
    "Лимфоциты %",
    "Моноциты %",
    "Эозинофилы %",
    "Базофилы %",
    "Нейтрофилы, абс.",
    "Лимфоциты, абс.",
    "Моноциты, абс.",
    "Эозинофилы, абс.",
    "Базофилы, абс.",
    "Глюкоза",
    "Общий белок",
    "Альбумин",
    "Мочевина",
    "Креатинин",
    "Мочевая кислота",
    "Общий билирубин",
    "Прямой билирубин",
    "Непрямой билирубин",
    "АЛТ (АлАТ)",
    "АСТ (АсАТ)",
    "ЩФ (щелочная фосфатаза)",
    "ГГТП",
    "ЛДГ",
    "Холестерин",
    "ЛПВП",
    "ЛПНП",
    "Триглицериды",
    "Кальций общий",
    "Калий",
    "Натрий",
    "Хлориды",
    "Фосфор",
    "Магний",
    "Протромбиновое время",
    "Протромбин по Квику",
    "МНО",
    "АЧТВ",
    "Фибриноген",
    "Тромбиновое время",
    "Антитромбин III",
    "D-димер",
    "С-реактивный белок",
    "Ревматоидный фактор",
    "b-ХГЧ общий",
    "ТТГ",
    "Т3",
    "Т4",
    "Пролактин",
    "ЛГ",
    "ФСГ",
    "Эстрадиол",
    "Тестостерон",
    "Кортизол",
    "Ретикулоциты",
    "Тромбокрит",
    "Средний объем тромбоцитов",
    "Фолиевая кислота",
    // Витамины
    "Витамин 25(ОН) D",
    "Витамин A",
    "Витамин B1",
    "Витамин B2",
    "Витамин B3",
    "Витамин B5",
    "Витамин B6",
    "Витамин B7",
    "Витамин B9",
    "Витамин B12",
    "Витамин C",
    "Витамин E",
    "Витамин K",
];

const nazvaniya_mapping: Record<string, string> = {
    // CBC/General
    "Гемоглобин": "hemoglobin",
    "Эритроциты": "erythrocytes",
    "MCV": "mcv",
    "RDW": "rdw",
    "MCH": "mch",
    "MCHC": "mchc",
    "Гематокрит": "hematocrit",
    "Тромбоциты": "platelets",
    "Лейкоциты": "wbc",
    "СОЭ": "esr",

    // WBC Differential
    "Нейтрофилы %": "neutrophils",
    "Палочкоядерные нейтрофилы": "band_neutrophils",
    "Сегментоядерные нейтрофилы": "segmented_neutrophils",
    "Лимфоциты %": "lymphocytes",
    "Моноциты %": "monocytes",
    "Эозинофилы %": "eosinophils",
    "Базофилы %": "basophils",
    "Нейтрофилы, абс.": "neutrophils_abs",
    "Лимфоциты, абс.": "lymphocytes_abs",
    "Моноциты, абс.": "monocytes_abs",
    "Эозинофилы, абс.": "eosinophils_abs",
    "Базофилы, абс.": "basophils_abs",

    // Biochemistry
    "Глюкоза": "glucose",
    "Общий белок": "protein_total",
    "Альбумин": "albumin",
    "Мочевина": "urea",
    "Креатинин": "creatinine",
    "Мочевая кислота": "uric_acid",
    "Общий билирубин": "bilirubin_total",
    "Прямой билирубин": "bilirubin_direct",
    "Непрямой билирубин": "bilirubin_indirect",
    "АЛТ (АлАТ)": "alt",
    "АСТ (АсАТ)": "ast",
    "ЩФ (щелочная фосфатаза)": "alkaline_phosphatase",
    "ГГТП": "ggt",
    "ЛДГ": "ldh",
    "Холестерин": "cholesterol",
    "ЛПВП": "hdl_cholesterol",
    "ЛПНП": "ldl_cholesterol",
    "Триглицериды": "triglycerides",
    "Кальций общий": "calcium_total",
    "Калий": "potassium",
    "Натрий": "sodium",
    "Хлориды": "chlorides",
    "Фосфор": "phosphorus",
    "Магний": "magnesium",

    // Coagulation
    "Протромбиновое время": "prothrombin_time",
    "Протромбин по Квику": "prothrombin_quick",
    "МНО": "inr",
    "АЧТВ": "aptt",
    "Фибриноген": "fibrinogen",
    "Тромбиновое время": "thrombin_time",
    "Антитромбин III": "antithrombin_iii",
    "D-димер": "d_dimer",

    // Immunology
    "С-реактивный белок": "crp",
    "Ревматоидный фактор": "rheumatoid_factor",

    // Hormones
    "b-ХГЧ общий": "b_hcg_total",
    "ТТГ": "tsh",
    "Т3": "t3",
    "Т4": "t4",
    "Пролактин": "prolactin",
    "ЛГ": "lh",
    "ФСГ": "fsh",
    "Эстрадиол": "estradiol",
    "Тестостерон": "testosterone",
    "Кортизол": "cortisol",

    // Other/Extended
    "Ретикулоциты": "reticulocytes",
    "Тромбокрит": "thrombocrit",
    "Средний объем тромбоцитов": "mpv",
    "Фолиевая кислота": "folic_acid",

    // Vitamins
    "Витамин 25(ОН) D": "vitamin_d",
    "Витамин A": "vitamin_a",
    "Витамин B1": "vitamin_b1",
    "Витамин B2": "vitamin_b2",
    "Витамин B3": "vitamin_b3",
    "Витамин B5": "vitamin_b5",
    "Витамин B6": "vitamin_b6",
    "Витамин B7": "vitamin_b7",
    "Витамин B9": "vitamin_b9",
    "Витамин B12": "vitamin_b12",
    "Витамин C": "vitamin_c",
    "Витамин E": "vitamin_e",
    "Витамин K": "vitamin_k",
};

// TypeScript version of the parse_blood_test_v2_ function
export async function parse_blood_test_v2_(files: File[]): Promise<any> {
    // return {'hemoglobin': {'value': 165.0, 'ref': '132 - 173'}, 'erythrocytes': {'value': 5.3, 'ref': '4.30 - 5.70'}, 'mcv': {'value': 91.1, 'ref': '80.0 - 99.0'}, 'rdw': {'value': 11.8, 'ref': '11.6 - 14.8'}, 'mch': {'value': 31.1, 'ref': '27.0 - 34.0'}, 'mchc': {'value': 34.2, 'ref': '32.0 - 37.0'}, 'hematocrit': {'value': 48.3, 'ref': '39.0 - 49.0'}, 'platelets': {'value': 326.0, 'ref': '150 - 400'}, 'wbc': {'value': 5.98, 'ref': '4.50 - 11.00'}, 'esr': {'value': 9.0, 'ref': '< 15'}, 'neutrophils': {'value': 40.2, 'ref': '48.0 - 78.0'}, 'band_neutrophils': null, 'segmented_neutrophils': null, 'lymphocytes': {'value': 48.5, 'ref': '19.0 - 37.0'}, 'monocytes': {'value': 8.0, 'ref': '3.0 - 11.0'}, 'eosinophils': {'value': 3.0, 'ref': '1.0 - 5.0'}, 'basophils': {'value': 0.3, 'ref': '< 1.0'}, 'neutrophils_abs': {'value': 2.4, 'ref': '1.78 - 5.38'}, 'lymphocytes_abs': {'value': 2.9, 'ref': '1.32 - 3.57'}, 'monocytes_abs': {'value': 0.48, 'ref': '0.20 - 0.95'}, 'eosinophils_abs': {'value': 0.18, 'ref': '0.00 - 0.70'}, 'basophils_abs': {'value': 0.02, 'ref': '0.00 - 0.20'}, 'glucose': null, 'protein_total': null, 'albumin': null, 'urea': null, 'creatinine': null, 'uric_acid': null, 'bilirubin_total': null, 'bilirubin_direct': null, 'bilirubin_indirect': null, 'alt': null, 'ast': null, 'alkaline_phosphatase': null, 'ggt': null, 'ldh': null, 'cholesterol': null, 'hdl_cholesterol': null, 'ldl_cholesterol': null, 'triglycerides': null, 'calcium_total': null, 'potassium': null, 'sodium': null, 'chlorides': null, 'phosphorus': null, 'magnesium': null, 'prothrombin_time': null, 'prothrombin_quick': null, 'inr': null, 'aptt': null, 'fibrinogen': null, 'thrombin_time': null, 'antithrombin_iii': null, 'd_dimer': null, 'crp': null, 'rheumatoid_factor': null, 'b_hcg_total': null, 'tsh': null, 't3': null, 't4': null, 'prolactin': null, 'lh': null, 'fsh': null, 'estradiol': null, 'testosterone': null, 'cortisol': null, 'reticulocytes': null, 'thrombocrit': null, 'mpv': null, 'folic_acid': null, 'vitamin_d': null, 'vitamin_a': null, 'vitamin_b1': null, 'vitamin_b2': null, 'vitamin_b3': null, 'vitamin_b5': null, 'vitamin_b6': null, 'vitamin_b7': null, 'vitamin_b9': null, 'vitamin_b12': null, 'vitamin_c': null, 'vitamin_e': null, 'vitamin_k': null, 'full_name': 'ДЖУНУСОВ ДИНМУХАМЕД САИНҰЛЫ', 'age': 31, 'sex': 'Мужской', 'date': '01.06.2024'}
    //
    // return {'hemoglobin': {'value': 114.0, 'ref': '117 - 160'}, 'erythrocytes': {'value': 4.32, 'ref': '3.8 - 5.3'}, 'mcv': {'value': 78.2, 'ref': '80 - 100'}, 'rdw': null, 'mch': {'value': 26.4, 'ref': '26.5 - 33.5'}, 'mchc': {'value': 33.7, 'ref': '31 - 38'}, 'hematocrit': {'value': 33.8, 'ref': '> 35'}, 'platelets': {'value': 205.0, 'ref': '150 - 400'}, 'wbc': {'value': 4.6, 'ref': '4.5 - 11'}, 'esr': {'value': 36.0, 'ref': '< 23'}, 'neutrophils': {'value': 74.0, 'ref': '47 - 72'}, 'band_neutrophils': null, 'segmented_neutrophils': null, 'lymphocytes': {'value': 14.0, 'ref': '19 - 37'}, 'monocytes': {'value': 9.0, 'ref': '2 - 9'}, 'eosinophils': {'value': 2.0, 'ref': '< 5'}, 'basophils': {'value': 0.0, 'ref': '< 1.2'}, 'neutrophils_abs': {'value': 3.38, 'ref': '1.5 - 7'}, 'lymphocytes_abs': {'value': 0.66, 'ref': '1 - 4.8'}, 'monocytes_abs': {'value': 0.42, 'ref': '< 0.7'}, 'eosinophils_abs': {'value': 0.1, 'ref': '< 0.45'}, 'basophils_abs': {'value': 0.01, 'ref': '< 0.1'}, 'glucose': null, 'protein_total': null, 'albumin': null, 'urea': null, 'creatinine': null, 'uric_acid': null, 'bilirubin_total': null, 'bilirubin_direct': null, 'bilirubin_indirect': null, 'alt': null, 'ast': null, 'alkaline_phosphatase': null, 'ggt': null, 'ldh': null, 'cholesterol': null, 'hdl_cholesterol': null, 'ldl_cholesterol': null, 'triglycerides': null, 'calcium_total': null, 'potassium': null, 'sodium': null, 'chlorides': null, 'phosphorus': null, 'magnesium': null, 'prothrombin_time': null, 'prothrombin_quick': null, 'inr': null, 'aptt': null, 'fibrinogen': null, 'thrombin_time': null, 'antithrombin_iii': null, 'd_dimer': null, 'crp': null, 'rheumatoid_factor': null, 'b_hcg_total': null, 'tsh': null, 't3': null, 't4': null, 'prolactin': null, 'lh': null, 'fsh': null, 'estradiol': null, 'testosterone': null, 'cortisol': null, 'reticulocytes': null, 'thrombocrit': null, 'mpv': null, 'folic_acid': null, 'vitamin_d': null, 'vitamin_a': null, 'vitamin_b1': null, 'vitamin_b2': null, 'vitamin_b3': null, 'vitamin_b5': null, 'vitamin_b6': null, 'vitamin_b7': null, 'vitamin_b9': null, 'vitamin_b12': null, 'vitamin_c': null, 'vitamin_e': null, 'vitamin_k': null, 'full_name': 'ТУРГАНБАЕВА САГЫНГАН РЫСКУЛОВНА', 'age': 63, 'sex': 'Женский', 'date': '29.05.2025'}

    if (!process.env.LLAMA_CLOUD_API_KEY) {
        throw new Error("LLAMA_CLOUD_API_KEY is not set");
    }

    if (!process.env.OPENAI_API_KEY) {
        throw new Error("OPENAI_API_KEY is not set");
    }

    let contents = "";
    for (const file of files) {
        console.log(file.name);
        const file_content = await file.arrayBuffer();
        const parser = new LlamaParseReader({ resultType: "markdown", language: 'ru' });
        const documents = await parser.loadDataAsContent([new Uint8Array(file_content)], { file_name: file.name });

        contents += documents[0];
    }
    // Записываем содержимое в файл для отладки
    fs.writeFileSync("parsed_blood_test_contents.txt", contents, "utf-8");

    const system_prompt = `You are a medical data parser. Extract full_name, age ("Жасы (Возраст):"), sex(Пол), date (Дата сдачи анализа) and also all analyte names ("названия анализов" or "Компонент"), their results ("результат" or "Нәтиже"), units ("единицы измерения"), and reference values ("Референс мағыналары(Референсные значения)") from the clinical blood test table(s) in the text.
        Return a JSON dictionary mapping the Russian analyte name to a dictionary of 'value' (as float or str), 'units' (as str), and, where available, 'ref' (reference range as str).
        If there is no analyte table or no blood test result, return an empty dictionary.`;

    const user_prompt = `
    В данном тексте в формате markdown содержатся таблицы с результатами лабораторных анализов на русском и казахском языках.
    Найди для каждого анализа из этого списка: ${JSON.stringify(nazvaniya_analizov)} -- значение "Результат" из текста (всегда числовое!),
    если такого анализа нет в тексте, верни None для этого ключа. Верни только Python словарь, ключи — из этого списка, значения — найденное значение (или None) и Референсные значения. Также full_name, age (всегда числовое!), sex(Пол: Мужской или Женский), and date (Дата сдачи анализа).
    Текст: '''${contents}'''
    `;

    const client = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY
    });

    const response = await client.chat.completions.create({
        model: "gpt-4.1",  // или "gpt-3.5-turbo", если нет доступа к gpt-4
        messages: [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    });
    // console.log(typeof response.choices[0].message.content)
    const answer_str = response.choices![0].message.content!.trim();
    const answer = eval(`(${answer_str})`);

    const final: any = {};
    for (const value of nazvaniya_analizov) {
        final[nazvaniya_mapping[value]] = answer[value] || null;
    }
    final["full_name"] = answer['full_name'];
    final["age"] = answer['age'];
    final["sex"] = answer['sex'];
    final["date"] = answer['date'];
    console.log(final);

    return final;
}
