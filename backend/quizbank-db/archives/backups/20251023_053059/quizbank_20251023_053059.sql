--
-- PostgreSQL database dump
--

\restrict cLXcZl7NSe9NRW6xldOA5eI3hnjcddoDIJrg667Uyjjcalv31jmSOvcyVKwl3GJ

-- Dumped from database version 15.14 (Debian 15.14-1.pgdg13+1)
-- Dumped by pg_dump version 15.14 (Debian 15.14-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: assessments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.assessments (
    assessment_id integer NOT NULL,
    course_id integer NOT NULL,
    assessment_type text NOT NULL,
    assessment_acadyear text,
    assessment_semester text,
    created_at timestamp without time zone DEFAULT now(),
    created_by integer
);


ALTER TABLE public.assessments OWNER TO postgres;

--
-- Name: assessments_assessment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.assessments_assessment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.assessments_assessment_id_seq OWNER TO postgres;

--
-- Name: assessments_assessment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.assessments_assessment_id_seq OWNED BY public.assessments.assessment_id;


--
-- Name: attachments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attachments (
    attachment_id integer NOT NULL,
    context_id integer,
    question_id integer,
    attachment_name character varying(255),
    attachment_type character varying(255)
);


ALTER TABLE public.attachments OWNER TO postgres;

--
-- Name: attachments_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.attachments_attachment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attachments_attachment_id_seq OWNER TO postgres;

--
-- Name: attachments_attachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.attachments_attachment_id_seq OWNED BY public.attachments.attachment_id;


--
-- Name: contexts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contexts (
    context_id integer NOT NULL,
    assessment_id integer NOT NULL,
    course_id integer NOT NULL,
    context_local_id text,
    context_text text,
    context_attachment text
);


ALTER TABLE public.contexts OWNER TO postgres;

--
-- Name: contexts_context_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contexts_context_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.contexts_context_id_seq OWNER TO postgres;

--
-- Name: contexts_context_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contexts_context_id_seq OWNED BY public.contexts.context_id;


--
-- Name: courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.courses (
    course_id integer NOT NULL,
    course_code text NOT NULL,
    course_name text
);


ALTER TABLE public.courses OWNER TO postgres;

--
-- Name: courses_course_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.courses_course_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.courses_course_id_seq OWNER TO postgres;

--
-- Name: courses_course_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.courses_course_id_seq OWNED BY public.courses.course_id;


--
-- Name: questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.questions (
    question_id integer NOT NULL,
    course_id integer,
    assessment_id integer,
    context_id integer,
    question_number text,
    sub_question_number text,
    question_text text NOT NULL,
    question_type character varying(50),
    option_a text,
    option_b text,
    option_c text,
    option_d text,
    option_e text,
    correct_answer text,
    explanation text,
    points numeric DEFAULT 1.0,
    difficulty character varying(50),
    concepts text,
    created_at timestamp without time zone DEFAULT now(),
    created_by integer,
    version_number integer DEFAULT 1,
    previous_version_id integer
);


ALTER TABLE public.questions OWNER TO postgres;

--
-- Name: questions_question_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.questions_question_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.questions_question_id_seq OWNER TO postgres;

--
-- Name: questions_question_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.questions_question_id_seq OWNED BY public.questions.question_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username text,
    password_hash text NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: assessments assessment_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assessments ALTER COLUMN assessment_id SET DEFAULT nextval('public.assessments_assessment_id_seq'::regclass);


--
-- Name: attachments attachment_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attachments ALTER COLUMN attachment_id SET DEFAULT nextval('public.attachments_attachment_id_seq'::regclass);


--
-- Name: contexts context_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contexts ALTER COLUMN context_id SET DEFAULT nextval('public.contexts_context_id_seq'::regclass);


--
-- Name: courses course_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses ALTER COLUMN course_id SET DEFAULT nextval('public.courses_course_id_seq'::regclass);


--
-- Name: questions question_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions ALTER COLUMN question_id SET DEFAULT nextval('public.questions_question_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: assessments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.assessments (assessment_id, course_id, assessment_type, assessment_acadyear, assessment_semester, created_at, created_by) FROM stdin;
1	73	Supervised	\N	\N	2025-10-22 05:47:27.132175	\N
2	1	Quiz2	2425	Sem1	2025-10-22 05:47:27.132175	\N
3	1	Quiz7	2425	Sem1	2025-10-22 05:47:27.132175	\N
4	20	Questions	\N	\N	2025-10-22 05:47:27.132175	\N
5	18	Questions	\N	\N	2025-10-22 05:47:27.132175	\N
6	1	Quiz4	2425	Sem1	2025-10-22 05:47:27.132175	\N
7	1	Quiz1	2425	Sem1	2025-10-22 05:47:27.132175	\N
8	1	Quiz8	2425	Sem1	2025-10-22 05:47:27.132175	\N
9	1	Final	2425	Sem1	2025-10-22 05:47:27.132175	\N
10	1	Midterm	2425	Sem1	2025-10-22 05:47:27.132175	\N
11	73	Simulation	\N	\N	2025-10-22 05:47:27.132175	\N
12	1	Quiz6	2425	Sem1	2025-10-22 05:47:27.132175	\N
13	17	Quiz1	\N	\N	2025-10-22 05:47:27.132175	\N
14	1	Quiz3	2425	Sem1	2025-10-22 05:47:27.132175	\N
15	73	Regression	\N	\N	2025-10-22 05:47:27.132175	\N
16	17	Quiz2	\N	\N	2025-10-22 05:47:27.132175	\N
17	1	Quiz5	2425	Sem1	2025-10-22 05:47:27.132175	\N
18	92	Questions	\N	\N	2025-10-22 05:47:27.132175	\N
\.


--
-- Data for Name: attachments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attachments (attachment_id, context_id, question_id, attachment_name, attachment_type) FROM stdin;
1	1	\N	winequality-white.csv	csv
2	2	\N	venv_paths.csv	csv
3	2	\N	winequality-red.csv	csv
4	1	\N	winequality-red.csv	csv
5	1	\N	venv_paths.csv	csv
6	2	\N	winequality-white.csv	csv
7	4	\N	DSA1101_Sem1_2425_Quiz7.R	r
8	5	\N	DSA1101_Sem1_2425_Quiz4_Figure1.png	image
9	6	\N	DSA1101_Sem1_2425_Quiz4_Figure2.png	image
10	7	\N	DSA1101_Sem1_2425_Quiz1_Figure1.png	image
11	11	\N	DSA1101_Sem1_2425_Final_Figure3.png	other
12	12	\N	DSA1101_Sem1_2425_Final_Figure4.png	image
13	11	\N	DSA1101_Sem1_2425_Final_Figure2.png	image
14	9	\N	DSA1101_Sem1_2425_Final_Figure1.png	image
15	13	\N	DSA1101_Sem1_2425_Midterm_Figure1.png	image
16	15	\N	DSA1101_Sem1_2425_Quiz6.R	r
17	18	\N	taiwan_dataset.csv	csv
18	17	\N	venv_paths.csv	csv
19	17	\N	taiwan_dataset.csv	csv
20	18	\N	venv_paths.csv	csv
21	19	\N	DSA1101_Sem1_2425_Quiz5_Figure1.png	image
22	\N	8	DSA1101_Sem1_2425_Quiz2_Figure1.png	image
23	\N	48	ST1131_Quiz1_Figure1.png	image
24	\N	97	ST1131_Quiz2_Figure5.png	image
25	\N	93	ST1131_Quiz2_Figure4.png	image
26	\N	89	ST1131_Quiz2_Figure2.png	image
27	\N	92	ST1131_Quiz2_Figure3.png	image
28	\N	89	ST1131_Quiz2_Figure1.png	image
29	\N	91	ST1131_Quiz2_Figure1.png	image
30	\N	96	ST1131_Quiz2_Figure5.png	image
31	\N	170	DSA1101_Sem1_2425_Quiz3_Figure1.png	image
32	\N	172	DSA1101_Sem1_2425_Quiz3_Figure1.png	image
33	\N	174	DSA1101_Sem1_2425_Quiz3_Figure1.png	image
34	\N	175	DSA1101_Sem1_2425_Quiz3_Figure2.png	image
35	\N	169	DSA1101_Sem1_2425_Quiz3_Figure1.png	image
36	\N	171	DSA1101_Sem1_2425_Quiz3_Figure1.png	image
37	\N	173	DSA1101_Sem1_2425_Quiz3_Figure1.png	image
38	\N	187	ST2137_Questions_Figure2.png	image
39	\N	188	ST2137_Questions_Figure3.png	image
40	\N	189	ST2137_Questions_Figure4.png	image
41	\N	185	ST2137_Questions_Figure1.png	image
\.


--
-- Data for Name: contexts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.contexts (context_id, assessment_id, course_id, context_local_id, context_text, context_attachment) FROM stdin;
1	1	73	1	```{r echo=FALSE}\nlibrary(reticulate)\ntmp_out <- include_supplement("venv_paths.csv")\ntmp_out <- include_supplement("winequality-red.csv", dir="../data/wine+quality/")\ntmp_out <- include_supplement("winequality-white.csv", dir="../data/wine+quality/")\ntmp_out <- include_supplement("wine_tree.png", dir="figs/")\n\nvenv_paths <- read.csv("venv_paths.csv")\nid <- match(Sys.info()["nodename"], venv_paths$nodename)\nuse_virtualenv(venv_paths$path[id])\n```\n\n```{python echo=FALSE}\nimport pandas as pd\nimport numpy as np\n\nfrom sklearn import tree\nfrom sklearn.model_selection import train_test_split\n\nwine_red = pd.read_csv("winequality-red.csv", delimiter=";" )\nwine_red['type'] = "red"\nwine_white = pd.read_csv("winequality-white.csv", delimiter=";")\nwine_white['type'] = "white"\n\n# remove spaces in column names:\ncol_names = ['fixed_acidity', 'volatile_acidity', 'citric_acid', 'residual_sugar',\n             'chlorides', 'free_sulfur_dioxide', 'total_sulfur_dioxide',\n             'density', 'pH', 'sulphates', 'alcohol', 'quality', 'type']\nwine2 = pd.concat([wine_red, wine_white], ignore_index=True)\nwine2.columns = col_names\n```\n\nThe (red and white) wine quality datasets from the unsupervised learning topic have been merged into a single dataframe with 6497 rows. A decision tree classifier has been fit to the dataset as follows:\n\n```{python}\nwine2.shape\n\nwine2.type.value_counts()\n\ny = [1 if x=="red" else 0 for x in wine2.type]\nX = wine2.iloc[:, 0:11]\nX_train,X_test,y_train,y_test = train_test_split(X, y, test_size=0.2,  random_state=14, stratify=y)\n```\n\nThe resulting decision tree consists of the following [rules](wine_tree.png):\n```{r echo=FALSE, out.width="2000px", fig.align="center", fig.cap="Decision tree"}\nknitr::include_graphics("wine_tree.png")\n\n```	venv_paths.csv, winequality-white.csv, winequality-red.csv
2	1	73	2	```{r echo=FALSE}\nlibrary(reticulate)\ntmp_out <- include_supplement("venv_paths.csv")\ntmp_out <- include_supplement("winequality-red.csv", dir="../data/wine+quality/")\ntmp_out <- include_supplement("winequality-white.csv", dir="../data/wine+quality/")\n\nvenv_paths <- read.csv("venv_paths.csv")\nid <- match(Sys.info()["nodename"], venv_paths$nodename)\nuse_virtualenv(venv_paths$path[id])\n```\n```{python echo=FALSE}\nimport pandas as pd\nimport numpy as np\n\nfrom sklearn import tree\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.metrics import ConfusionMatrixDisplay\n\nwine_red = pd.read_csv("winequality-red.csv", delimiter=";" )\nwine_red['type'] = "red"\nwine_white = pd.read_csv("winequality-white.csv", delimiter=";")\nwine_white['type'] = "white"\n\n# remove spaces in column names:\ncol_names = ['fixed_acidity', 'volatile_acidity', 'citric_acid', 'residual_sugar',\n             'chlorides', 'free_sulfur_dioxide', 'total_sulfur_dioxide',\n             'density', 'pH', 'sulphates', 'alcohol', 'quality', 'type']\nwine2 = pd.concat([wine_red, wine_white], ignore_index=True)\nwine2.columns = col_names\n```\n\nThe (red and white) wine quality datasets from the unsupervised learning topic \nhave been merged into a single dataframe with 6497 rows. A decision tree \nclassifier has been fit to the dataset as follows:\n\n```{python fig.align="center", fig.cap="Confusion matrix"}\ny = [1 if x=="red" else 0 for x in wine2.type]\nX = wine2.iloc[:, 0:11]\nX_train,X_test,y_train,y_test = train_test_split(X, y, test_size=0.2, random_state=14, stratify=y)\n\nclf = tree.DecisionTreeClassifier(max_depth=4)\nclf.fit(X_train, y_train)\n\ny_pred_train = clf.predict(X_train)\nConfusionMatrixDisplay.from_predictions(y_train, y_pred_train, labels=clf.classes_, cmap='bone');\n```	venv_paths.csv, winequality-white.csv, winequality-red.csv
3	2	1	1	In 1990, 1200 post-menopausal women were recruited for a study to\ninvestigate the effect of a Post-Menopausal Hormone (PMH) on the\nincidence of breast cancer (200 users and 1000 non-users). \nGiven a data set of 1200 women, breast_cancer.csv, in which we concern the columns below.\nbbd: Status having breast cancer, 1= Yes and 0 = No\nagemenop (Age): The age of the woman at menopausal\npmh: Status whether or not the woman use PMH (post-menopausal hormone). 2 = No and 3 = Yes\nbmi: The body mass index\n\nPurpose: We want to form a model/classifier that help us to predict the status of having breast cancer for women, based on their information of Age, PMH and BMI. 	\N
4	3	1	1	Data files <churn.csv> is provided on Canvas.\nPlease open the R code file attached <Quiz7.R> and run the code to answer the questions below.\nAll the log calculation mentioned in this quiz is the natural log (base e).\nNote: to run the code file smoothly, you might need to:\nDownload the data file above.\nSet working directory in R to the folder that contains the data file: setwd()	DSA1101_Sem1_2425_Quiz7.R
5	6	1	1	Consider data set <Smarket.csv>. One would want to split this data set into two parts randomly: one part is used to form a model, and other part is used to test the goodness of fit of the model. R code is given in the photo.	DSA1101_Sem1_2425_Quiz4_Figure1.png
6	6	1	2	There are 9 students with the names are: A, B, C, D, E, F, G, H and I. We would want to form 3 groups where each group has 2 students by a random way. The R code is given in the photo below.	DSA1101_Sem1_2425_Quiz4_Figure2.png
7	7	1	1	In the R code file for Topic 1, <Topic1_Rcode.R>, there is a part of code as below:\ndata1<-read.csv("C:/Data/crab.txt",sep = "", header = TRUE)\n\ndata1[1:8,] #first 8 rows. The output is below.	DSA1101_Sem1_2425_Quiz1_Figure1.png
8	8	1	1	Data set: <hdbresale_cluster.csv>\n\nWe would cluster all the flats in the data set into groups.	\N
9	9	1	1	Use set.seed(888) for questions in R.\n\nNo R code is required. Type your answers as comments in the R code file.\nIn 1990, 1200 randomly selected post-menopausal women were recruited for a study to\ninvestigate the effect of using Post-Menopausal Hormone (PMH) on the incidence of breast\ncancer. 200 of them were randomly chosen to be the users and the rest 1000 were the\nnon-users.\nThe table below summarizes the results after 5 years.	DSA1101_Sem1_2425_Final_Figure1.png
10	9	1	2	A dataset collected contains information of patients and their cancer status. Let Column Y be the response variable (cancer status) with two categories, 0 and 1, where 1 = diseased and 0 = no-diseased. Let p denote P(Y= diseased).	\N
11	9	1	3	Use set.seed(888) for questions in R.\n\nConsider a dataset about female horseshoe crabs during their mating season. Researchers want to investigate the male crabs that group around the female and potentially fertilize her eggs (called satellites). The table below gives the description for\neach variable in this study.\nThe first ten rows of the dataset is given in Figure 1.\n\n!(DSA1101_Sem1_2425_Final_Figure2.png)\n\nA model was fitted for the dataset given, called model M. The summary output for model M is given in Figure 2.\n\n!(DSA1101_Sem1_2425_Final_Figure3.png )\n\nNote: For the questions that follow, report numerical answers to three signicant figures if they are smaller than one and to three decimal places if they are larger than one.	DSA1101_Sem1_2425_Final_Figure2.png, DSA1101_Sem1_2425_Final_Figure3.png 
12	9	1	4	Consider a dataset about car evaluation where the quality of a car is evaluated based on some information from the record. Dataset is given in the file car-eval-dsa1101.csv \nThe table below gives the description for each variable in this study.\n\n!(DSA1101_Sem1_2425_Final_Figure4.png)\n\nFor the questions below,\n- load the dataset into R and name it as df.\n- report numerical answers to three signicant gures if they are smaller than one and to three decimal places if they are larger than one.\n- For all the models/classiers in the following questions, there is no need to split the dataset given into train set and test set.\n- For all the models/classiers in the following questions, use the six columns buying to safety as the input features.	DSA1101_Sem1_2425_Final_Figure4.png
13	10	1	1	(50 points) The data file patient_satisfaction.csv is a random sample collected from a hospital about the satisfactory of patients about the hospital's service when they were discharged. The data set includes information about patient's age, the score of illness severity, the anxiety score, and the status if the patient went through surgery (1) or only had medical treatment (0). The given file contains columns with names listed below.\n\n!(DSA1101_Sem1_2425_Midterm_Figure1.png)\n\n- please run function setwd() in a separate line (if you need it) when importing the data set into R.\n- use set.seed(310). You get penalty of (-2) points if you don't have it.\n- the names given in bold below MUST be used in your R code.\n- please report numerical answers to at least three signicant gures if it's smaller than one (e.g. 0.0123) and to three decimal places if it's larger than one (e.g. 2.345).\n\nLoad the file patient_satisfaction.csv into R and name it as data.	DSA1101_Sem1_2425_Midterm_Figure1.png
14	10	1	2	(10 points) Alena Lee is working for a company where her current salary is $50,000 annually and the salary is increased 5% every year.\nSo far, until end of 2024, she has a saving amount of $30,000.\nShe plans to form a start-up company which will requires an initial amount of $100,000.\n\nNote: The proportions of saving salary should be up to 2 decimal places only.	\N
15	12	1	1	Data files <bank-sample.csv> and <bank-sample-test.csv> are provided on Canvas. \nPlease open the R code file attached <Quiz6.R> and run the code to answer the questions below. \nNote: to run the code file smoothly, you might need to:\nSet working directory: setwd()\nInstall packages: install.packages(“e1071”)	DSA1101_Sem1_2425_Quiz6.R
16	14	1	1	Consider data set <crab.csv> where we are interested in satell -  the number of male crabs grouped around a female horse shoe crab during the mating season (called satellite). The possible regressors are the weight (kg) and the width (cm) of the female crab; the female crab's color (categorical, 2 = light; 3 = medium, 4 = dark, and 5 = darker).\nData set was imported into R and a model with 3 variables weight, width and color was built. 	\N
17	15	73	1	In the Rmd file:\n{r echo=FALSE}\nlibrary(reticulate)\ntmp_out <- include_supplement("venv_paths.csv")\ntmp_out <- include_supplement("taiwan_dataset.csv", dir="../data")\n\nvenv_paths <- read.csv("venv_paths.csv")\nid <- match(Sys.info()["nodename"], venv_paths$nodename)\nuse_virtualenv(venv_paths$path[id])\n\nSuppose that the following simple linear regression model has been fitted to the \nTaiwan real estate data from topic 05:\n\n$$\nY = \\beta_0 + \\beta_1 \\ln (X_1) + e\n$$\n\nwhere $X_1$ corresponds to distance to the nearest MRT. The following output \nwas obtained from Python:\n\n```{python echo=FALSE}\nimport pandas as pd\nimport numpy as np\nimport statsmodels.api as sm\nfrom statsmodels.formula.api import ols\n\nre2 = pd.read_csv("taiwan_dataset.csv")\n\nre2['ldist'] = np.log(re2.dist_MRT)\nlm_2 = ols('price ~ ldist', data=re2).fit()\nprint(lm_2.summary())\n```	venv_paths.csv,\ntaiwan_dataset.csv
18	15	73	2	r echo=FALSE}\nlibrary(reticulate)\ntmp_out <- include_supplement("venv_paths.csv")\ntmp_out <- include_supplement("taiwan_dataset.csv", dir="../data")\n\nvenv_paths <- read.csv("venv_paths.csv")\nid <- match(Sys.info()["nodename"], venv_paths$nodename)\nuse_virtualenv(venv_paths$path[id])\n\nSuppose that the following two simple linear regression models are fitted to the Taiwan real estate data from topic 05:\n\n\\begin{eqnarray}\nY &=& \\beta_0 + \\beta_1 \\ln (X_1) + e \\; \\text{( model 1 )}\\\\\n\\ln Y &=& \\beta_0 + \\beta_1 \\ln (X_1) + e \\: \\text{( model 2 )}\n\\end{eqnarray}\n\nwhere $X_1$ corresponds to distance to the nearest MRT. The following output was obtained from Python:\n\n{python echo=FALSE}\nimport pandas as pd\nimport numpy as np\nimport statsmodels.api as sm\nfrom statsmodels.formula.api import ols\n\nre2 = pd.read_csv("taiwan_dataset.csv")\n\nre2['lprice'] = np.log(re2.price)\nre2['ldist'] = np.log(re2.dist_MRT)\n\nlm_1 = ols('price ~ ldist', data=re2).fit()\nprint(lm_1.summary())\n\nlm_2 = ols('lprice ~ ldist', data=re2).fit()\nprint(lm_2.summary())	venv_paths.csv,\ntaiwan_dataset.csv
19	17	1	1	Functions in R: rpart(), rpart.plot().\nConsider again the dataset <bank-sample.csv> given in the lecture of Topic 5. One would want to build a model (a decision tree) which help to predict if a customer will subscribe the bank’s service, based on 8 factors (8 columns): job, marital, education, default, housing, loan, contact and poutcome.\n\nTo answer the questions below, please use the R code of Topic 5 to understand the data and to plot the tree as given in the photo below. 	DSA1101_Sem1_2425_Quiz5_Figure1.png
\.


--
-- Data for Name: courses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.courses (course_id, course_code, course_name) FROM stdin;
1	DSA1101	Introduction to Data Science
2	DSA2101	Essential Data Analytics Tools: Data Visualisation
3	DSA3101	Data Science in Practice
4	DSA3361	Inferential Data Analytics
5	DSA3362	Predictive Data Analytics
6	DSA4211	High Dimensional Statistical Analysis
7	DSA4212	Optimisation for Large‑Scale Data Driven Inference
8	DSA4213	Natural Language Processing for Data Science
9	DSA4262	Sense‑Making Case Analysis: Health and Medicine
10	DSA4263	Sense‑Making Case Analysis: Business and Commerce
11	DSA4264	Sense‑Making Case Analysis: Public Policy and Society
12	DSA4265	Sense‑Making Case Analysis: Economics
13	DSA4266	Sense‑Making Case Analysis: Science and Technology
14	DSE1101	Introductory Data Science for Economics
15	DSE3101	Practical Data Science for Economics
16	HS2914	How to Teach Humans and Machines to Talk
17	ST1131	Introduction to Statistics and Statistical Computing
18	ST2131	Probability
19	ST2132	Mathematical Statistics
20	ST2137	Statistical Computing and Programming
21	ST2334	Probability and Statistics
22	ST3131	Regression Analysis
23	ST3232	Design and Analysis of Experiments
24	ST3236	Stochastic Processes I
25	ST3239	Survey Methodology
26	ST3244	Demographic Methods
27	ST3246	Statistical Models for Actuarial Science
28	ST3247	Simulation
29	ST3248	Statistical Learning I
30	ST4231	Computer Intensive Statistical Methods
31	ST4233	Linear Models
32	ST4234	Bayesian Statistics
33	ST4238	Stochastics Processes II
34	ST4245	Statistical Methods for Finance
35	ST4248	Statistical Learning II
36	ST4250	Multivariate Statistical Analysis
37	ST4253	Applied Time Series Analysis
38	DSS5101	Principles of Sustainability
39	DSS5102	Advanced Regression and Time Series Analysis
40	DSS5103	Geospatial Data Analysis
41	DSS5104	Machine Learning and Predictive Modelling
42	DSS5105	Data Science Projects in Practice
43	DSS5201	Data Visualisation
44	DSS5202	Sustainable Systems Analysis
45	DSS5203	ESG Data for Sustainable Finance and Investments
46	DSS5210	Research/Industry Project I
47	DSS5211	Research/Industry Project II
48	ST5201X	Statistical Foundations of Data Science
49	ST5202	Applied Regression Analysis
50	ST5202X	Applied Regression Analysis
51	ST5203	Design of Experiments
52	ST5209X	Analysis of Time Series Data
53	ST5211X	Sampling from Finite Populations
54	ST5188	Advanced Data Science Project
55	ST5207	Nonparametric Regression
56	ST5212	Survival Analysis
57	ST5213	Advanced Categorical Data Analysis
58	ST5218	Advanced Statistical Methods in Finance
59	ST5221	Stochastic Processes and Applications
60	ST5225	Statistical Analysis of Networks
61	ST5226	Spatial Statistics
62	ST5227	Applied Statistical Learning
63	ST5229	Deep Learning in Data Analytics
64	ST5230	Applied Natural Language Processing
65	ST5290	Data Science Industry Project
66	ST6101	Advanced Statistical Theory
67	ST6102	Advanced Statistical Theory II
68	ST6103	Advanced Probability Theory
69	ST6104	Statistical Models
70	ST6105	Computational Statistics
71	ST6120	Graduate Seminar Module
72	ST6241	Topics I
73	IND5003	Data Analytics for Sense Making
74	ST5201	Statistical Foundations of Data Science
92	Template	Template
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.questions (question_id, course_id, assessment_id, context_id, question_number, sub_question_number, question_text, question_type, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, points, difficulty, concepts, created_at, created_by, version_number, previous_version_id) FROM stdin;
1	1	12	15	1	\N	How many explanatory variables are there in the Naïve Bayes classifier “nb_model”?	MCQ	6	7	8	9	10	E	data set “banktrain” has 11 columns (after dropping 6 unwanted columns).\nModel was formed as \nnb_model <- naiveBayes( subscribed ~ . , data = banktrain)\nwhere the response variable “subscribed” depends on a dot. This dot is to replace for “ALL OTHER COLUMNS” in data = banktrain. Hence, there are 10 columns used as explanatories in the model.	1.0	low	Supervised Learning, Data Manipulation, Naïve Bayes	2025-10-22 05:47:27.159819	\N	1	\N
2	1	12	15	2	\N	The values in “nb_prediction” are the class labels (no/yes) for each test point in the test data. True or False?	T/F	True	False	\N	\N	\N	B	It’s the probabilities, since type = “raw” is specified in the command\nnb_prediction <- predict(nb_model, newdata = banktest[  , -11], type ='raw')\nIf we want to get the class labels (no/yes) then we should specify type = “class”.	1.0	low	Supervised Learning, Model Validation, Naïve Bayes	2025-10-22 05:47:27.159819	\N	1	\N
3	1	12	15	3	\N	Write R code to get the predicted class labels for the data points in banktest and report the number of points be predicted as “yes” in the blank.\nNote: only report the answer, not include the code in the blank provided.	SRQ	\N	\N	\N	\N	\N	5	predicted.class <- predict(nb_model, newdata = banktest[  , -11], type ='class')\ntable(predicted.class)\n# 5 out of 100 points (or customers) be predicted as “yes”.	1.0	med	Supervised Learning, Data Manipulation, Naïve Bayes	2025-10-22 05:47:27.159819	\N	1	\N
4	1	12	15	4	\N	Continuing with the R code for Question 3 above, write R code to form a confusion matrix between the predicted class label and the real class label of the test set. Calculate and report the accuracy in the blank.\nNote: only report the answer, not include the code in the blank provided.	SRQ	\N	\N	\N	\N	\N	0.9 or 90%	confusion.matrix  = table(predicted.class, banktest[  , 11])\n\naccuracy = sum(diag(confusion.matrix)) / sum(confusion.matrix)\n\naccuracy\n# 0.9	1.0	med	Model Validation, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
5	1	2	3	1	\N	In order to know if we should use variable Age in the model/classifier, we should explore the association between the response variable with Age. True or False?	T/F	True	False	\N	\N	\N	A	\N	1.0	low	Supervised Learning, Basic Concepts in Statistics, EDA	2025-10-22 05:47:27.159819	\N	1	\N
6	1	2	3	2	\N	How to explore the association between the response bbd and age?	MCQ	Box plot of age for two groups of bbd	Histogram of age	Correlation coefficient of bbd and age	Scatter plot for bbd and age	\N	A	\N	1.0	low	Data Manipulation, Basic Concepts in Statistics, EDA	2025-10-22 05:47:27.159819	\N	1	\N
7	1	2	3	3	\N	How to explore the association between the response bbd and pmh	MRQ	Box plot of pmh for two groups of bbd	Contingency table with conditional probabilities of having breast cancer for different categories of pmh	Odds ratio	Correlation coefficient of pmh and bbd	\N	B,C	\N	1.0	low	Basic Concepts in Statistics, Data Manipulation, EDA	2025-10-22 05:47:27.159819	\N	1	\N
8	1	2	3	4	\N	Given the photo. Which of the following statements is correct.\n\n!(DSA1101_Sem1_2425_Quiz2_Figure1.png)	MCQ	The probability of not having cancer (bbd = 0) is 1.4 times the probability of having cancer.	The probability of not having cancer (bbd = 0) among non-PMH users (pmh = 2) is 1.4 times the probability of not having cancer among PMH users (pmh = 3).	The probability of having cancer (bbd = 0) among non-PMH users (pmh = 2) is 1.4 times the probability of having cancer among PMH users (pmh = 3).	The odds of not having cancer (bbd = 0) among non-PMH users (pmh = 2) is 1.4 times the odds of not having cancer among PMH users (pmh = 3).	\N	D	\N	1.0	low	Basic Concepts in Statistics, EDA	2025-10-22 05:47:27.159819	\N	1	\N
9	18	5	\N	1	\N	From a collection of nine paintings, four are to be selected to hang side-by-side on a gallery wall in positions 1, 2, 3 and 4. In how many ways can this be done?	MCQ	3024	6561	24	\N	\N	A	\N	1	low	Combinatorics, Permutations (Ordered Selection)	2025-10-22 05:47:27.159819	\N	1	\N
10	18	5	\N	2	\N	A group of 60 freshmen are to be randomly assigned into two classes of 30 students each, one on the first floor and one on the second floor. In how many ways can this be done?	MCQ	60C30	(60C30) / 2!	2! X (60C30)	\N	\N	A	\N	1	low	Combinations (Unordered Selection), Binomial Coefficient, Combinatorics	2025-10-22 05:47:27.159819	\N	1	\N
11	18	5	\N	3	\N	Suppose we have with us a biased coin. In other words, the probability of heads is p, where p >0.5. We flip the coin twice, and define the following events:\nA1: we observe head followed by a tail\nA2: we observe a tail followed by a head.\nWhat is P(A1 | A1 U A2)?	MCQ	0.5	p	1-p	\N	\N	A	\N	1	low	Conditional Probability, Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
12	18	5	\N	4	\N	If 8 identical blackboards are to be divided among 4 schools, how many divisions are possible?\n\nAnswer: 8! / 4!4!	T/F	True	False	\N	\N	\N	B	\N	1	med	Stars and Bars (Identical Items), Combinatorics	2025-10-22 05:47:27.159819	\N	1	\N
13	18	5	\N	5	\N	If 8 distinct blackboards are to be divided equally among 4 schools, how many possible assignments are there?	MCQ	8! / (2!2!2!2!) 	8C4	8!/4!	\N	\N	A	\N	1	med	Permutations, Multinomial Coefficient (Distinct Items), Combinatorics	2025-10-22 05:47:27.159819	\N	1	\N
14	18	5	\N	8	\N	A fair coin is tossed independently 10 times. Define the following events:\nAk: the k-th toss is heads\nS: the total number of heads observed in the 10 tosses is even. (Note that 0 is an even number).\nWhat is P(S | A1 A2 A3 ... A10)?	MCQ	True	False	(0.5)^10	\N	\N	A	\N	1	med	Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
15	18	5	\N	9	\N	Two players, A and B, alternately and independently flip a coin and the first player to obtain a head wins. Assume player A flips first. Define Ei to be the event that head appears first on the i-th toss. Which of the following statements is true about the sequence of events Ei?	MCQ	E2 is a proper subset of E1	E1 is a proper subset of E2	Neither of the above statements are true.	\N	\N	C	\N	1	med	Sequence of Events, Game theory, Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
16	18	5	\N	10	\N	Suppose that p(x) and q(x) are two distinct pmfs. Then for any b such that 0 <b <1, r(x) = bp(x) + (1-b)q(x) is also a pmf.	T/F	True	False	\N	\N	\N	A	\N	1	low	PMF Axioms, Random Variables, Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
17	18	5	\N	12	\N	Two fair six-sided dice are rolled. Let X be the product of the two dice. What is P(X >= 33)?	MCQ	1/36	33/36	3/36	\N	\N	A	\N	1	low	Probability on Sample Space (Counting Outcomes), Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
18	18	5	\N	15	\N	A deck of playing cards has 52 cards. Four of these cards are Aces. Suppose that a well-shuffled deck of cards is dealt out. What is the probability that the 14th card dealt out is an Ace?	MCQ	1/13	1/4	1/52	\N	\N	A	\N	1	low	Position Independence, Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
19	18	5	\N	19	\N	Let X be a random variable denoting the number of children in a family. X has support {1,2,3,4}, and pmf given by \np(1)\tp(2)\tp(3)\tp(4)\n0.1\t0.25\t0.35\t0.3\nA child from this family is chosen at random (i.e. all children within a family are equally likely to be selected). Let E be the event that the eldest child is chosen. Find P(X=1 | E).	MCQ	0.42	0.1	0.24	\N	\N	C	\N	1	high	Conditional Probability, Random Variables, Conditional Probability (Baye's Rule)	2025-10-22 05:47:27.159819	\N	1	\N
20	18	5	\N	20	\N	An urn has n white and m black balls. Balls are randomly withdrawn without replacement, one at a time, until a total of k white balls have been withdrawn, where k <= n. The random variable X is the total number of balls that have been withdrawn. Which of the following events is equivalent to {X = r}, where r is an integer in the support of X?	MCQ	There are k - 1 white balls in the first r-1 draws, and the r-th draw is a white ball.	There are r balls drawn.	There are k white balls in the first r draws.	\N	\N	A	\N	1	med	Random Variables, Conditional Probability, Negative Binomial 	2025-10-22 05:47:27.159819	\N	1	\N
21	18	5	\N	21	\N	Let E, F and G be three events from a sample space. Match the following descriptions to the events regarding E, F and G below. There is only one matching description for each event.\n\n1. E occurs.\n2. At least two of the events occur.\n3. Exactly two events occur.\n4. The empty set occurs.\n5. None of the three events occur.\n6. Only E occurs.\n\n1. (E U F U G)c\n2. EF U EG U FG	SRQ	\N	\N	\N	\N	\N	1. 5\n2. 2	\N	1	low	Set Operations and Events, Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
22	18	5	\N	22	\N	Let E, F and G be three events from a sample space. Match the following descriptions to the events regarding E, F and G below. There is only one matching description for each event.\n1. E occurs.\n2. At least two of the events occur.\n3. Exactly two events occur.\n4. Exactly one of the events occurs.\n5. Only E occurs.\n6. At least one of the events occurs.\n\n1. E U F U G\n2. E Fc Gc	SRQ	\N	\N	\N	\N	 	1. 6\n2. 5	\N	1	low	Set Operations and Events, Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
23	18	5	\N	23	\N	A fair coin is tossed independently n times, where n >= 2. Define the following events:\nAk: the k-th toss is heads.\nSn: the total number of heads observed in the n tosses is even. (Note that 0 is an even number).\nIs the collection of events A1, A2, A3, ... An, Sn independent?\nHint: Consider P(Sn | A1 A2 A3 ... An)	T/F	True	False	\N	\N	\N	B	\N	1	low	Event independence,  Conditional Probability 	2025-10-22 05:47:27.159819	\N	1	\N
24	18	5	\N	24	\N	Suppose that A and B are independent events such that the probability that neither occurs is a, and the probability that B occurs is b. Find P(A).	MCQ	a/(1-b)	(1-b-a)/(1-b)	ab	\N	\N	B	\N	1	med	Probability Rules (De Morgan's & Independence), Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
25	18	5	\N	25	\N	A fair coin is tossed independently n times, where n >= 2. Define the following events:\nAk: the k-th toss is heads.\nWhat is P(A1 A2 A3 A4 ... An)?	MCQ	1/2	(1/2)^n	k! / n!	\N	\N	B	\N	1	low	Event independence,  Conditional Probability 	2025-10-22 05:47:27.159819	\N	1	\N
26	18	5	\N	29	\N	Suppose that A and B are mutually exclusive, and P(A) >0 and P(B) >0. Which of the following statements is false?	MCQ	P(A|B)=0	A and B are independent.	A and B are dependent.	\N	\N	B	\N	1	low	Mutually Exclusive, Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
27	18	5	\N	30	\N	Suppose that A and B are events with positive probability. Determine if the following statement is true or false:\nIf A and B are not mutually exclusive, then they are independent.	T/F	True	False	\N	\N	\N	B	\N	1	low	Mutually Exclusive, Event Independence, Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
28	18	5	\N	31	\N	Suppose that A and B form a partition of the sample space, and P(A) >0 and P(B) >0. Which of the following statements is false?	MCQ	P(A | Bc) = 1	A and B are independent.	A and B are dependent.	\N	\N	B	\N	1	low	Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
29	18	5	\N	32	\N	A mobile phone manufacturing company has two factories X and Y. Factories X and Y produce 30% and 70% of all mobile phones respectively. 9% of the phones produced by factory X are defective, and 1% of the phones produced by factory Y are defective. If a phone bought from the company is found to be defective, what is the probability that it was produced by factory X?	MCQ	0.79	0.027	0.3	\N	\N	A	\N	1	med	Bayes' Theorem, Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
30	18	5	\N	35	\N	A and B are mutually exclusive events. Further, P(A) = 0.3 and P(B) = 0.2. What is the probability that both events occur?	MCQ	There is insufficient information to compute this probability.	0.06	0	\N	\N	C	\N	1	low	Mutually Exclusive, Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
31	18	5	\N	36	\N	How many ways can we arrange the letters in the word "VISITING" such that no two "I"s are adjacent?   \nHint: \nExperiment 1: Permute the non-I letters.\nExperiment 2: Choose where to put the I's.	MCQ	6720	2400	480	\N	\N	B	\N	1	med	Permutations with Constraints, Combinatorics	2025-10-22 05:47:27.159819	\N	1	\N
32	18	5	\N	37	\N	How many ways can we arrange the letters in the word "VISITING"?	MCQ	6720	2400	480	\N	\N	A	\N	1	low	Permutations with Identical Items, Combinatorics	2025-10-22 05:47:27.159819	\N	1	\N
33	18	5	\N	38	\N	Independent trials are performed indefintely, where each trial consists of rolling a pair of fair six-sided dice, and then summing the values on the dice at each trial.\nThus, if we observe (1,2), (3,4) and (6,6) in the first three trials, then the outcomes of the first three trials are recorded as 3, 7 and then 12.\nWe define En to be the event that no 5 or 7 appears on the first n-1 trials and a 5 appears on the n-th trial. Is En an increasing or decreasing sequence?	MCQ	An increasing sequence.	A decreasing sequence.	It is neither increasing or decreasing.	\N	\N	C	\N	1	med	Sequence of Events, Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
34	18	5	\N	41	\N	There are n socks in a drawer, 3 of which are red. What is the value of n if, when 2 of the socks are chosen randomly, the probability that they are both red is 1/2?	MCQ	n=4	n=6	n=5	\N	\N	A	\N	1	med	Combinatorics, Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
35	18	5	\N	42	\N	Suppose that the random variable X has support {1, 2, 3, 4, 5, .... }. For i in this set, the pmf is given by \nP(X = i) = 1/i - 1/(i+1)\nIf we let Y = 2 - X, what is the pmf of Y evaluated at -5? In other words, what is P(Y = -5)?	MCQ	1/56	1/20	-1/5	\N	\N	A	\N	1	low	PMF of a Transformed Random Variable, Random Variables	2025-10-22 05:47:27.159819	\N	1	\N
36	18	5	\N	43	\N	Suppose that the random variable X has support {1, 2, 3, 4, 5, .... }. For i in this set, the pmf is given by \nP(X = i) = 1/i - 1/(i+1)\nIf we let Y = 1 if X <= 2 and 0 otherwise, what is P(Y = 0)?	MCQ	True	1/2	1/3	\N	\N	C	\N	1	low	CDF, Random Variables	2025-10-22 05:47:27.159819	\N	1	\N
37	18	5	\N	44	\N	There are 4 TV repairmen and 8 TV repair jobs. If it is possible for a single repairman to do multiple jobs, how many possible assignments of repairmen to jobs are there?	MCQ	8^4	4^8	8C4	\N	\N	B	\N	1	low	Combinatorics	2025-10-22 05:47:27.159819	\N	1	\N
38	18	5	\N	45	\N	If P(A) = 1/4 and P(B) = 1/3, then \nP(AB) is less than or equals to 7/12\nTrue or False?	T/F	True	False	\N	\N	\N	A	\N	1	low	Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
39	18	5	\N	46	\N	If P(A)=1/3 and P(Bc)=1/4 then it is still possible for A and B to be disjoint.	T/F	True	False	\N	\N	\N	B	\N	1	low	Probability Axioms	2025-10-22 05:47:27.159819	\N	1	\N
40	18	5	\N	47	\N	A company has two factories X and Y. Factories X and Y produce 40% and 60% of all watches respectively. 2% of the watches produced by factory X are defective, and 3% of the watches produced by factory Y are defective. If a watch bought from the company is found to be defective, what is the probability that it was produced by factory Y?	MCQ	0.69	0.018	0.026	\N	\N	A	\N	1	med	Bayes' Theorem, Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
41	18	5	\N	48	\N	An urn has n white and m black balls. Balls are randomly withdrawn without replacement, one at a time, until a total of k white balls have been withdrawn, where k <= n. The random variable X is the total number of balls that have been withdrawn. What is the support of X?	MCQ	{1, 2, 3, ... , n+m}	{k, k+1, ... , n+m}	{1, 2, 3, ..., k}	\N	\N	B	\N	1	med	Random Variables	2025-10-22 05:47:27.159819	\N	1	\N
42	17	13	\N	1	\N	A quantitative variable can be categorized into categorical variables.	T/F	True	False	\N	\N	\N	A	\N	1	low	Basic Concepts in Statistics, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
43	17	13	\N	2	\N	Postal code in Singapore has values that are recorded as numbers so it is a quantitative variable.	T/F	True	False	\N	\N	\N	B	\N	1	low	Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
44	17	13	\N	3	\N	A bar plot (bar chart) is often used to visualize a quantitative variable, like height, age or weight.	T/F	True	False	\N	\N	\N	B	\N	1	low	EDA, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
45	17	13	\N	4	\N	A histogram can only portray the frequency of values of a quantitative variable.	T/F	True	False	\N	\N	\N	B	\N	1	low	EDA, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
46	17	13	\N	5	\N	Given variable height, the shape of the histogram in frequency and the histogram in probability of variable height are the same.	T/F	True	False	\N	\N	\N	A	\N	1	low	EDA, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
47	17	13	\N	6	\N	Which of the following is an appropriate method for summarising ordinal data?	MCQ	Frequency Table	Histogram	\N	\N	\N	A	\N	1	low	Basic Concepts in Statistics, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
48	17	13	\N	7	\N	Consider the following dataset of observations:\n0.54, 0.42, 0.85, 1.57, 1.09, 0.75, 1.28, 1.86, 2.51, 1.94\nWhich of the following is the correct histogram for this data?\n!(ST1131_Quiz1_Figure1.png)	MCQ	a	b	c	d	\N	B	\N	1	low	EDA, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
49	17	13	\N	8	\N	Variable \\"smoking level\\" has 3 levels that has values recorded in numbers (0, 1 and 3), where 0 = “no smoking”, 1 = “<= 5 cigarettes a day” and 3 = “more than 5 cigarettes a day”. It is a categorical variable.	T/F	True	False	\N	\N	\N	A	\N	1	low	Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
50	17	13	\N	9	\N	Which of the following variables are continuous, when the measurement is as precise as possible?	MRQ	Age of mother	Number of children in a family	Cooking time for preparing dinner	Latitude of a city	Longtitude of a city	A, C, D, E	\N	1	low	Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
51	17	13	\N	10	\N	Scores on a difficult exam have a mean of 57 and a standard deviation of 20. The instructor boosts all the scores by 20 points before awarding grades. What is the standard deviation of the new boosted scores?",	SRQ	\N	\N	\N	\N	\N	20	\N	1	low	Basic Concepts in Statistics, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
52	17	13	\N	11	\N	The mean of a sample is always one of the observed values.	T/F	True	False	\N	\N	\N	B	\N	1	low	Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
53	17	13	\N	12	\N	The Harvard Medical School study included about 22,000 male physicians. Whether a given individual would be assigned to take aspirin or the placebo was determined by flipping a coin. As a result, about 11,000 physicians were assigned to take aspirin and about 11,000 to take the placebo. The researchers summarized the results of the experiment using percentages. Of the physicians taking aspirin, 0.9% had a heart attack, compared to 1.7% of those taking the placebo. Based on the observed results, the study authors concluded that taking aspirin reduces the risk of having a heart attack. Match the aspect of the study that pertains to descriptive or inferential statistics respectively.\n\n1. The researchers summarized the results... 0.9% had a heart attack, compared to 1.7% of those taking the placebo.\n2. Based on the observed results, the study authors concluded that taking aspirin reduces the risk of having a heart attack.	SRQ	\N	\N	\N	\N	\N	1. Descriptive statistics.\n2. Inferential statistics.	\N	1	low	Basic Concepts in Statistics, Inference	2025-10-22 05:47:27.159819	\N	1	\N
54	17	13	\N	13	\N	1% of the data are above the first percentile.	T/F	True	False	\N	\N	\N	B	\N	1	low	Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
55	17	13	\N	14	\N	The inter-quartile range can be viewed as the range for the middle 50% of the data.	T/F	True	False	\N	\N	\N	A	\N	1	low	Basic Concepts in Statistics, EDA	2025-10-22 05:47:27.159819	\N	1	\N
56	17	13	\N	15	\N	Which of the following measures is/are resistant to outliers?	MRQ	Median	Mean	\N	\N	\N	A	\N	1	low	Basic Concepts in Statistics, EDA	2025-10-22 05:47:27.159819	\N	1	\N
57	17	13	\N	16	\N	What measures of center and variability are the most appropriate to describe a symmetric distribution?	MRQ	Mean	Median	Interquartile range	Standard deviation	\N	A, D	\N	1	low	Basic Concepts in Statistics, EDA	2025-10-22 05:47:27.159819	\N	1	\N
58	17	13	\N	17	\N	What measures of center and variability are the most appropriate to describe a skewed distribution?	MRQ	Mean	Median	Interquartile range	Standard deviation	\N	B, C	\N	1	low	Basic Concepts in Statistics, EDA	2025-10-22 05:47:27.159819	\N	1	\N
59	1	9	9	1	1	Calculate and report the conditional probabilities that help to investigate if using PMH increases the chance of getting breast cancer.	Code	\N	\N	\N	\N	\N	\N	\N	4	low	Basic Concepts in Statistics, EDA, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
60	1	9	9	1	2	Calculate and report the odds ratio for the table above. Interpret it in the context of this study.	Code	\N	\N	\N	\N	\N	\N	\N	6	med	Basic Concepts in Statistics, EDA\t	2025-10-22 05:47:27.159819	\N	1	\N
61	1	9	10	2	1	In order to get the prediction of p of the test points using a tted 10-NN classifier, the R code is of the form\npred.prob = knn(train, test, cl, k = 10,___)\nwhere in the blank space, we add	MCQ	type = prob	type = class	prob = TRUE	type = response	type = raw	\N	\N	2.5	low	Supervised Learning, KNN, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
62	1	9	10	2	2	Using a fitted decision tree, named fit, the prediction of p of the test points is obtained by\npred.prob = predict(fit, new.data = test, ___)\nwhere in the blank space, we add	MCQ	type = prob	type = class	prob = TRUE	type = response	type = raw	\N	\N	2.5	low	Supervised Learning, Decision Trees, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
63	1	9	10	2	3	Using a fitted Naive Bayes classier, named nb, the prediction of pof the test points\nis obtained by\npred.prob = predict(nb, new.data = test, ___)\nwhere in the blank space, we add	MCQ	type = prob	type = class	prob = TRUE	type = response	type = raw	\N	\N	2.5	low	Supervised Learning,Naïve Bayes, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
64	1	9	10	2	4	Using a fitted logistic regression, named lr, the prediction of p of the test points is\nobtained by\npred.prob = predict(lr, new.data = test, ___)\nwhere in the blank space, we add	MCQ	type = prob	type = class	prob = TRUE	type = response	type = raw	\N	\N	2.5	low	Supervised Learning , Logistic Regression, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
65	1	9	11	3	1	Type the equation of model M into the R code file as comments. Explain in detail if any notation is used in the equation.	Code	\N	\N	\N	\N	\N	\N	\N	2	med	Linear Modeling, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
66	1	9	11	3	2	Report the coeffecient of variable color in model M and interpret it.	Code	\N	\N	\N	\N	\N	\N	\N	2	med	Linear Modeling, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
67	1	9	11	3	3	Report the coecient of variable weight in model M and interpret it. Is it signicant in model M? Explain.	Code	\N	\N	\N	\N	\N	\N	\N	2	med	Linear Modeling, Basic Concepts in Statistics, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
68	1	9	11	3	4	Calculate and report the odds ratio of having satellites between two crabs below:\nCrab A: weight = 3 kg, color = light;\nCrab B: weight = 2 kg, color = dark.	Code	\N	\N	\N	\N	\N	\N	\N	4	high	Supervised Learning, Logistic Regression, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
69	1	9	12	4	1	Write code to create a new column for df named status, where status equal to 1 if quality of car evaluation is high, and status equal to 0 otherwise.	Code	\N	\N	\N	\N	\N	\N	\N	2	low	Data Manipulation 	2025-10-22 05:47:27.159819	\N	1	\N
70	1	9	12	4	2	Let m denote a vector of possible values for argument minsplit which is from 25 up to 50. Write code to fit a decision tree (using Information Gain) that helps to predict status of car evaluation using the dataset given for each value of minsplit in m.\nFor each tree fitted, write code to obtain the values of TPR and FNR.	Code	\N	\N	\N	\N	\N	\N	\N	6	high	Supervised Learning, Decision Trees, Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
71	1	9	12	4	3	Which is the best value of minsplit such that the value of TPR of the tree built from that minsplit is at least 0.9. Write code to show how to determine the best value of minsplit.	Code	\N	\N	\N	\N	\N	\N	\N	4	med	Supervised Learning, Decision Trees, Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
72	1	9	12	4	4	With the value of minsplit chosen in Question 3, write code to fit a decision tree, to be named as DT. Report the name of the most important variable in that tree.	Code	\N	\N	\N	\N	\N	\N	\N	3	low	Supervised Learning, Decision Trees	2025-10-22 05:47:27.159819	\N	1	\N
73	1	9	12	4	5	Write code to plot the ROC curve of the tree DT. Derive and report the value of AUC.	Code	\N	\N	\N	\N	\N	\N	\N	5	med	Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
74	1	9	12	4	6	We now use the naive Bayes classifier for the dataset given. Let status be the response variable. Write code to form the classifier, to be named as NB.	Code	\N	\N	\N	\N	\N	\N	\N	2	low	Supervised Learning, Naïve Bayes, Data Manipulation 	2025-10-22 05:47:27.159819	\N	1	\N
75	1	9	12	4	7	Write code to calculate the precision of NB for the given dataset using a threshold δ= 0.1.	Code	\N	\N	\N	\N	\N	\N	\N	4	med	Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
76	1	9	12	4	8	Write code to plot the ROC curve of the classier NB. Derive and report the value of AUC.	Code	\N	\N	\N	\N	\N	\N	\N	4	med	Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
77	1	9	12	4	9	Since all the input features are ordered, we can fit a logistic regression for status, by considering each feature as a quantitative variable.\nWrite code to transform buying to numeric with values 1, 2, 3, and 4 for the categories low, med, high, and vhigh, respectively.	Code	\N	\N	\N	\N	\N	\N	\N	3	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
78	1	9	12	4	10	Using status as the response variable, write code to form a logistic regression model for it (called LR), using the six input features given.	Code	\N	\N	\N	\N	\N	\N	\N	3	low	Supervised Learning, Logistic Regression, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
79	1	9	12	4	11	Under model LR, compare the odds of having status being 1 (high quality) between a car that has big luggage boot and that of a car having small luggage boot, given that they both have the same information for other features.	Code	\N	\N	\N	\N	\N	\N	\N	4	med	Supervised Learning, Logistic Regression, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
80	1	9	12	4	12	Write code to calculate the precision of model LR for the given dataset using a threshold δ= 0.1.	Code	\N	\N	\N	\N	\N	\N	\N	5	med	Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
81	1	9	12	4	13	Write code to plot the ROC curve of model LR. Derive and report the value of AUC.	Code	\N	\N	\N	\N	\N	\N	\N	5	med	Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
82	1	9	12	4	14	Since all the input features are ordered, we can fit a KNN classier for status, by considering each feature as a quantitative variable.\nWrite code to standardize the six input features, and store them in a data frame named data.x.	Code	\N	\N	\N	\N	\N	\N	\N	3	med	Data Manipulation, Supervised Learning, KNN	2025-10-22 05:47:27.159819	\N	1	\N
83	1	9	12	4	15	Consider KNN classiers with k being the odd numbers from 3 up to 43. Write code to form those classiers and store the values of TPR and FNR for each value of k.	Code	\N	\N	\N	\N	\N	\N	\N	4	high	Supervised Learning, KNN, Model Validation, Data Manipulation 	2025-10-22 05:47:27.159819	\N	1	\N
84	1	9	12	4	16	Report the value of k that its TPR is at least 0.9 and its FNR is non-zero.	Code	\N	\N	\N	\N	\N	\N	\N	2	low	Supervised Learning, KNN, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
85	1	9	12	4	17	With the value of k determined in Question 16, write code to form a KNN classier and find its precision using a threshold δ= 0.1.	Code	\N	\N	\N	\N	\N	\N	\N	3	med	Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
86	1	9	12	4	18	Write code to plot the ROC curve of the KNN classier in Question 17. Derive and report the value of AUC.	Code	\N	\N	\N	\N	\N	\N	\N	3	med	Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
87	1	9	12	4	19	Write code to create a plot that has all the four ROC curves created in Questions 5, 8, 13, 18 where each curve should have a different color and a legend box is included in the plot.	Code	\N	\N	\N	\N	\N	\N	\N	3	med	Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
88	1	9	12	4	20	Among all the four ROC curves, which curve has highest AUC value?	Code	\N	\N	\N	\N	\N	\N	\N	2	low	Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
89	17	16	\N	1	\N	Match the following variables to the boxplots that follow.\nVariable 1: ST1232 Exam score (median = 90.71, minimum = 57.9, maximum = 99.4)\nVariable 2: IQ score (median = 99)\nBoxplot 1: !(ST1131_Quiz2_Figure1.png)\nBoxplot 2: !(ST1131_Quiz2_Figure2.png)	SRQ	\N	\N	\N	\N	\N	Boxplot 1: Variable 1,\nBoxplot 2: Variable 2	\N	1	low	EDA, Basic Concepts in Statistics, Boxplot	2025-10-22 05:47:27.159819	\N	1	\N
90	17	16	\N	2	\N	Many years back, the scores of the ST1131 final exam had the following five-number summary:\nMinimum: 78.3\nLower quartile: 83.6\nMedian: 87.2\nUpper quartile: 88.8\nMaximum: 92.3\nWould a boxplot of this dataset show any outliers?	MCQ	Yes	No	\N	\N	\N	B	\N	1	low	EDA, Basic Concepts in Statistics, Interquartile Range	2025-10-22 05:47:27.159819	\N	1	\N
91	17	16	\N	3	\N	Consider the following boxplot. If you were told that the distribution is unimodal, what skew would be present in it?\n!(ST1131_Quiz2_Figure1.png)	MCQ	Symmetric	Left Skewed	Right Skewed	\N	\N	B	\N	1	low	EDA, Boxplot	2025-10-22 05:47:27.159819	\N	1	\N
92	17	16	\N	4	\N	A study is performed to assess the efficacy of two new drugs for reducing systolic blood pressure in patients. There are three treatment groups - one used a placebo, while the other two groups used drug A and drug B. Study the SPSS output below. \n\nWhat is the interquartile range for treatment A and B group?\nGive your answer to 2 decimal places.\n!(ST1131_Quiz2_Figure3.png)	SRQ	\N	\N	\N	\N	\N	Treatment A: 18.00\nTreatment B: 27.75	\N	1	low	EDA, Basic Concepts in Statistics, Interquartile Range	2025-10-22 05:47:27.159819	\N	1	\N
93	17	16	\N	5	\N	Varying levels of treatment were administered to a group of ill males and females, and their response to the illness was measured using a response variable. The scatterplot of the data is shown below, where shapes are used to distinguish gender. Which gender has a lower mean response?\n!(ST1131_Quiz2_Figure4.png)	MCQ	Males	Females	\N	\N	\N	A	\N	1	low	EDA, Visualization	2025-10-22 05:47:27.159819	\N	1	\N
94	17	16	\N	6	\N	If two quantitative variables have a correlation value of 1 then the scatter plot of them fits a straight line.	T/F	True	False	\N	\N	\N	A	\N	1	low	Basic Concepts in Statistics, Correlation	2025-10-22 05:47:27.159819	\N	1	\N
95	17	16	\N	7	\N	Two variables X and Y have correlation value 0.278. That means, X and Y are surely linearly correlated.	T/F	True	False	\N	\N	\N	B	\N	1	low	Basic Concepts in Statistics, Correlation	2025-10-22 05:47:27.159819	\N	1	\N
96	17	16	\N	8	\N	Consider Breast Cancer data (Topic2_EDA_4.pdf) which have variables "pmh.use" (Yes/No) and "cancer" (Absent/Present).\nThe contingency table of percentage is extracted from the lecture note and given below (please revise the data and the values given in the data) before answering the question.\n!(ST1131_Quiz2_Figure5.png)\nWhat is the value 60.5% referring to?	MCQ	Percentage of not having cancer among PMH users	Percentage of PMH users among those not having cancer	\N	\N	\N	A	\N	1	low	EDA, Basic Concepts in Statistics, Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
97	17	16	\N	9	\N	Consider Breast Cancer data (Topic2_EDA_4.pdf) which have variables "pmh.use" (Yes/No) and "cancer" (Absent/Present). \nThe contingency table of percentage is extracted from the lecture note and given below (please revise the data and the values given in the data) before answering the question.\n!(ST1131_Quiz2_Figure5.png)\nIf the researchers want to investigate if using PMH would increase the chance of having breast cancer, then which pair of percentages should they compare?	MRQ	Percentage of having cancer among PMH users	Percentage of not having cancer among PMH users	Percentage of having cancer among non-PMH users	\N	\N	A, C	\N	1	low	EDA, Basic Concepts in Statistics, Association between Variables	2025-10-22 05:47:27.159819	\N	1	\N
98	73	15	17	1	\N	What is the null hypothesis corresponding to the $t$-statistic with value -21.959?	MCQ	$H_0:\\; \\beta_1 = 0$	$H_0:\\; \\beta_0 = 0$	$H_0:\\; \\hat{\\beta}_1 = 0$	$H_0:\\; \\hat{\\beta}_0 = 0$	\N	A	A is correct.\nB corresponds to the test for the intercept in the model, not the coefficient for ldist.\nC and D: Hypothesis tests are for population parameters, not estimates, which are denoted with a hat symbol.	1.0	low	Regression, Inference, Hypothesis Testing, T-Test, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
99	73	15	17	2	\N	What is the test statistic corresponding to the following hypothesis test?\n\\begin{eqnarray}\nH_0:\\; \\beta_0 &=& 0 \\\\\nH_1:\\; \\beta_0 & \\ne & 0 \n\\end{eqnarray}	MCQ	95.0169	36.034	-21.959	482.2	2.52e-71	B	A is the estimate of $\\hat{\\beta}_0$.\nB is indeed the value of the test statistic.\nC is the $t$-statistic for testing of the coefficient $\\beta_1$ is 0.\nD is $F$-statistic for testing of the coefficient $\\beta_1$ is 0.\nE is the $p$-value for the $F$-statistic.	1.0	low	Regression, Inference, Hypothesis Testing, T-Test, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
100	73	15	17	3	\N	Which of the following is/are correct interpretations of the fitted equation: \n$$\n\\hat{Y} = \\hat{\\beta}_0 + \\hat{\\beta}_1 \\ln (X_1)\n$$	MRQ	Every one unit increase in distance-to-MRT is associated with an average increase of $\\beta$-units in $Y$.	Every one unit increase in distance-to-MRT is associated with an average increase of $\\hat{\\beta}$-units in $Y$.	Every doubling of distance-to-MRT is associated with an average increase of $\\ln(2) \\times \\hat{\\beta}$-units in $Y$.	Every one unit increase in $\\ln(X)$ is associated with an average increase of $\\hat{\\beta}$-units in $Y$.	\N	B, D	Suppose that $\\hat{Y} = \\hat{\\beta}_0 + \\hat{\\beta}_1 \\ln(X_1)$. Then if we double $X' = 2 X_1$,\n\\begin{eqnarray}\n\\hat{Y}' &=& \\hat{\\beta}_0 + \\hat{\\beta}_1 \\ln(X') \\\\ \n&=& \\hat{\\beta}_0 + \\hat{\\beta}_1 \\ln(2 X) \\\\  \n&=& \\hat{\\beta}_0 + \\hat{\\beta}_1 (\\ln(2) + \\ln(X)) \\\\  \n&=& \\hat{\\beta}_1 \\ln(2) + \\hat{Y}\n\\end{eqnarray}	1.0	low	Regression, Inference, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
101	73	15	17	4	\N	What is the estimated mean for a new observation with distance to MRT 1.5km? Show all the Python code used.	Code	\N	\N	\N	\N	\N	new_df = sm.add_constant(pd.DataFrame({'dist_MRT' : 1500.0}, index=[0]))\nnew_df['ldist']  = np.log(new_df.dist_MRT)\npredictions_out = lm_2.get_prediction(new_df)\n\nprint(f"The estimated mean is {predictions_out.predicted_mean[0]:.3f}")	\N	1.0	low	Regression, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
102	73	15	17	5	\N	What is the 90% confidence interval for a mean for a new observation with distance to MRT 800m?	Code	\N	\N	\N	\N	\N	new_df = sm.add_constant(pd.DataFrame({'dist_MRT' : 800.0}, index=[0]))\nnew_df['ldist']  = np.log(new_df.dist_MRT)\npredictions_out = lm_2.get_prediction(new_df)\nupper,lower = predictions_out.conf_int(alpha=0.10).reshape(2,)\n\nprint(f"The estimated lower and upper limits are ({lower:.3f}, {upper:.3f}).")	\N	1.0	med	Regression, Inference, Basic Concepts in Statistics, Confidence Interval	2025-10-22 05:47:27.159819	\N	1	\N
103	73	15	17	6	\N	Suppose that I am hunting for a new property, but I am not willing to spend more than 50,000 NT dollars per ping. What is the closest distance to an MRT that I can afford, according to the above model?	Code	\N	\N	\N	\N	\N	\\begin{eqnarray}\n95.0169 - 8.9235 \\ln(X) &\\le& 50 \\\\\nX &\\ge& 155.21\n\\end{eqnarray}	\N	1.0	med	Regression, Data Manipulation, Algebra	2025-10-22 05:47:27.159819	\N	1	\N
104	73	15	17	7	\N	Consider the broken line regression model that we fitted to the Taiwan real estate price data, with housing age as the explanatory variable. In the notes, we used the value 25 years. In the following function we can input the age we wish to set the breakpoint at. The function should return the adjusted $R^2$ for the corresponding regression model.\n\n```\ndef housing_break(age, data):\n    tmp_data = data.copy()\n    tmp_data['x3'] = [ _______(1)_________  for x in data.house_age]\n    lm_age_mrt_2 = ols('price ~ house_age + x3', data=tmp_data).fit()\n    return lm_age_mrt_2.___(2)_____\n```\n\nFill in the two blanks with the appropriate Python expressions to get the function working.	Code	\N	\N	\N	\N	\N	1. (x - age) if x > age else 0\n2. rsquared_adj	\N	1.0	low	Regression, Model Validation, Basic Concepts in Statistics, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
114	1	7	7	2	\N	To let R recognizes the first column of data frame above as a categorical, we need to sue a function to convert this column into a factor (*). True or False?\n(*) such as function as.factor(), or factor(). 	T/F	True	False	\N	\N	\N	A	Both as.factor() and factor() could be used.	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
115	1	7	7	3	\N	Brandon uses function as.factor() to transform the first column of data frame above into a categorical variable by the code below.\ncolor = as.factor(data1$color)\n\nThen, now, the first column of “data1” is recognized by R as categorical. True or False?	T/F	True	False	\N	\N	\N	B	This line of code by Brandon creates a new variable, named as “color”, which factorizes the column “color” of “data1”. Hence, this new variable with the name “color” is a categorical variable and it is outside of “data1”.\nTo verify, you can run the code \nis.numeric(data1$color)\nThen R will show “TRUE” to confirm that the first column of “data1” is still NUMERIC, not categorical. Instead, you will have FALSE when running\nis.numeric(color)	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
105	73	15	18	8	\N	An analyst concludes that model (2) has a better fit since the $R^2$ is larger (0.579 in the latter compared with 0.539 in the former). Which of the following statements is correct?	MCQ	The analyst is correct. The two $R^2$ values are comparable because they are both based on the same dataset.	The analyst is correct. The two $R^2$ values are comparable because they both use the same independent variable.	The analyst is mistaken. The two $R^2$ values cannot be compared because the dependent variables are different.	The analyst is correct that model (2) fits better, but the reason is incorrect - the adjusted $R^2$ should be used instead.	\N	C	The formula for $R^2$ is $$\nR^2 = 1 - \\frac{SS_{Res}}{SS_T} = \\frac{SS_{Reg}}{SS_T} = \\frac{\\sum_{i=1}^n (\\hat{Y_i}  - \\bar{Y})^2}{\\sum_{i=1}^n (Y_i  - \\bar{Y})^2}\n$$ However, the two models use different $Y$ values. The $SS_T$ is different! Hence it does not make sense to compare the two $R^2$ values directly.\n\nA is incorrect.\nB: $R^2$ calculation does not depend on the independent variable.\nC: This is correct.\nD: With simple linear regression, it is conventional to use the unadjusted $R^2$. However, the issue is not with this. Adjusted $R^2$ adjusts for the number of independent variables, but assumes the dependent variable is the same.	1.0	med	Regression, Model Validation, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
106	73	15	17	9	\N	Consider the broken line regression model that we fitted to the Taiwan real estate price data, with housing age as the explanatory variable. In the notes, we used the value 25 years. In the following function we can input the age we wish to set the breakpoint at. The function returns the adjusted $R^2$ for the corresponding regression model.\n\n```\ndef housing_break(age, data):\n    tmp_data = data.copy()\n    tmp_data['x3'] = [ (x - age) if x > age else 0 for x in data.house_age]\n    lm_age_mrt_2 = ols('price ~ house_age + x3', data=tmp_data).fit()\n    return lm_age_mrt_2.rsquared_adj\n```\n\nUse the function above to identify the "best" value of `age` to use in the model. Name one downside of using this value.	Code	\N	\N	\N	\N	\N	def housing_break(age, data): \n    tmp_data = data.copy() \n    tmp_data['x3'] = [ (x - age) if x > age else 0 for x in data.house_age] \n    lm_age_mrt_2 = ols('price ~ house_age + x3', data=tmp_data).fit() \n    return lm_age_mrt_2.rsquared_adj\n\nage_grid = np.arange(0, 45, step = 0.1)\nr2_vals = [housing_break(x, re2) for x in age_grid]\n\nid = np.argmax(r2_vals)\n\nprint(f"The optimal house age is {age_grid[id]:.1f}")\n\nOne downside of using this value is that it could be overfitted to this particular dataset.	\N	1.0	high	Regression, Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
107	73	15	17	10	\N	Which of the following statement(s) regarding the *raw* residuals is (are) true? Remember that raw residuals are given by\n$$\nr_i = Y_i - \\hat{Y}_i\n$$	MCQ	There is exactly one residual greater than 50.	There are at least two residuals less than -30.	The mean of the raw residuals for properties transacted in 2012 is approximately -2.6 (1 d.p.)	The mean of the raw residuals for properties transacted in 2013 is approximately 2.6 (1 d.p.)	The mean of the raw residuals is approximately 0.0 (1 d.p.)	A, C, E	import pandas as pd\nimport numpy as np\n\nimport statsmodels.api as sm\nfrom statsmodels.formula.api import ols\n\nfrom scipy import stats\n\nre2 = pd.read_csv("taiwan_dataset.csv")\nre2['ldist'] = np.log(re2.dist_MRT)\n\nre2['year_int'] = re2.trans_date.astype(int)\nre2['year_s'] = re2.year_int.astype(str)\n\nlm_3 = ols('price ~ ldist', data=re2).fit()\nre2['r_3'] = re2.price - lm_3.fittedvalues\n\nre2.r_3.groupby(re2.year_s).describe()\n\nre2['abs_r_3'] = np.abs(re2.r_3)\n\nre2.sort_values(by='abs_r_3', ascending=False).head(n=5)	1.0	low	Regression, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
108	1	17	19	1	\N	The node circled in red color (no 1789/2000) in the figure above means	MCQ	The sample size is 2000 but only 1789 are available for data analysis.	The sample size is 2000 and 1789 of them belong to category “no” of the response variable “subscribe” (did not subscribe). The rest belongs to other category.\n	The sample size is 2000 but only 1789 of them has information about “poutcome”.	There are 1789 among 2000 observations in this tree.	\N	B	\N	1.0	low	Supervised Learning, Decision Trees	2025-10-22 05:47:27.159819	\N	1	\N
109	1	17	19	2	\N	The leaf node in the square (no 1763/1942) means	MCQ	Among 1789 customers saying “no” to the subscription of the bank service, the probability that they belong to poutcome = failure, other or unknown is 1763/1942.	Among all the 2000 customers, there are 1942 of them has poutcome = failure, other or unknown. Among those 1942 customers, 1763 of them did not subscribe the bank service.	\N	\N	\N	B	\N	1.0	low	Supervised Learning, Decision Trees	2025-10-22 05:47:27.159819	\N	1	\N
110	1	17	19	3	\N	The node where the red arrow is pointing (yes 32/58) means	MRQ	If a customer has poutcome = success then without information of any other factors, we can predict that the customer will subscribe the bank service with probability 32/58.	Among 2000 customers, there are total of 58 customers has poutcome = success. And among these 58 customers, there are 32 of the subscribed the bank service.	Among the 1789 customers that did not subscribe the bank service, there are 58 of them has poutcome = success. 	\N	\N	A,B	\N	1.0	low	Supervised Learning, Decision Trees	2025-10-22 05:47:27.159819	\N	1	\N
111	1	17	19	4	\N	The leaf node in the red triangle (yes 8/8) means	MRQ	If a customer has education = primary or unknown, then s/he is predicted to subscribe the bank service with probability 100%.	There are 8 customers that has poutcome = success and education = primary or unknown but there is no information if they subscribed the bank service or not.	There are 58 customers has poutcome = success in the sample, and there are 8 among those 58 customers has education = primary or unknown that all subscribed the bank service.\n	If a customer has poutcome = success and education = primary or unknown, then we can predict that s/he will subscribe the bank service with probability 100%.	\N	C,D	\N	1.0	low	Supervised Learning, Decision Trees	2025-10-22 05:47:27.159819	\N	1	\N
112	1	17	19	5	\N	The leaf node above the purple arrow (no 26/45) means	MRQ	Among 1789 customers that did not subscribe the bank service, there are 26 of them that have the job = admin, blue-collar, management, retired, services or technician.	If a customer that has poutcome  = success; and education = secondary or tertiary; and job = admin, blue-collar, management, retired, services or technician; then we can predict that the probability s/he will not subscribe the bank service is 26/45.	Among 1789 customers that did not subscribe the bank service, the probability of them that have poutcome = success; and education = secondary or tertiary; and job = admin, blue-collar, management, retired, services or technician is 26/45.	Among 2000 customers, there are 58 of them that have poutcome = success; and among those 58, there are 50 of them that have education = secondary or tertiary; and there are 45 among those 50 that have job = admin, blue-collar, management, retired, services or technician; and there are 26 among those 45 that did not subscribe the bank service.	\N	B,D	\N	1.0	low	Supervised Learning, Decision Trees	2025-10-22 05:47:27.159819	\N	1	\N
113	1	7	7	1	\N	Column “color” in the data frame above is recognized by R as a categorical variable. True or False?	T/F	True	False	\N	\N	\N	B	The values of column “color” are numeric, hence, by default, R considers this column as a numeric column/variable.	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
116	1	7	7	4	\N	After running the line of code on Q3, Brandon continues with two lines of code below:\ncolor*2 # LINE 1: to multiply every element of “color” by 2\n\ndata1$color*2 # LINE 2: to multiply every element of column “color” in “data1” by 2\n\nBoth lines of code above will not produce answers. True or False?	T/F	True	False	\N	\N	\N	B	LINE 1 will produce “NA”. This is because object “color” is memorized by R as categorical. Hence, multiplication is not possible for its categories.\nHowever, for column “color” inside “data1”, data1$color, it is still recognized by R as a numeric column. Hence, multiplication is possible for it.	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
117	1	7	7	5	\N	If now you run the code\nspine\n then you will get an error from R. True or False?	T/F	True	False	\N	\N	\N	A	This is because R now knows “data1” but it doesn’t know the name of each column inside “data1” yet. 	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
118	1	7	7	6	\N	Fact: function attach(df) helps R to know every names inside data frame “df”, to know the values of each column, as well as the properties (categorical/numeric) of  each column.\nAfter all the code above was run, Brandon continues with function attach() as below.\nattach(data1)\nNow, there is no error appearing when Brandon runs the code\nspine\nTrue or False?	T/F	True	False	\N	\N	\N	A	Because after function attach(data1) was run, R now knows that “spine” is a column inside “data1” and R knows all the values of that column.	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
119	1	7	7	7	\N	Brandon continues with the code below.\nspine = as.factor(data1$spine)\n\nAfter this line of code is run, column “spine” of “data1” now become a categorical variable. True or False?	T/F	True	False	\N	\N	\N	B	Back to Q3 and the answer of Q3. This code creates a new object/vector, named “spine” OUTSIDE of “data1”, it uses column “spine” of “data1” and factorizes it. So, this “spine” is a categorical variable. \nHowever, the column “spine” INSIDE “data1” is still memorized by R as a numeric column. This memory was created when function attach(data1) was run.	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
120	1	7	7	8	\N	To let R recognizes column “spine” inside “data1” as a categorical column, we should use\ndata1$spine = as.factor(data1$spine)\nTrue or False?	T/F	True	False	\N	\N	\N	A	\N	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
121	73	1	\N	1	\N	Which of the following is an example of a classification problem?	MCQ	Predicting tomorrow’s stock price based on today’s price.	Predicting the rental price of an apartment.	Identifying whether a tumor is present in an MRI scan.	Estimating how much a customer will spend on their next purchase.	\N	C	A, B, D: Regression\nC: Classification	1.0	low	Supervised Learning, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
122	73	1	\N	2	\N	Which preprocessing technique is suitable when your dataset contains categorical variables?	MCQ	Scaling	Principal Component Analysis (PCA)	One-Hot Encoding	Feature Extraction	\N	C	A is for converting transforming numerical variables to have the same scale.\nB is used for:\n  * dimension reduction - reducing the number of continuous variables to a smaller subset, that \n    consists of linear combinations of the original ones.\n  * removing correlation between numeric variables - this can improve prediction.\nC converts a single column containing the character version of the categorical\n  variable into a set of 0/1 columns representing it. ML methods require numeric inputs..\nD is a process whereby only important columns for prediction are retained.	1.0	low	Data Manipulation, Supervised Learning	2025-10-22 05:47:27.159819	\N	1	\N
123	73	1	\N	3	\N	What is the shape of the *training dataset* (without the labels) when the following \ncode is executed?\n\n```{python eval=FALSE}\nfrom sklearn.model_selection import train_test_split\nimport numpy as np\n\n# Generate sample data\nX = np.random.rand(100, 5)  \ny = np.random.randint(0, 2, 100)  \n\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\nprint(X_train.shape)\n```	MCQ	(80, 5)	(100, 5)	(20, 5)	(80, 2)	\N	A	\N	1.0	low	Supervised Learning, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
124	73	1	\N	4	\N	Which method in scikit-learn estimators is used to estimate the parameters of a model using the training data?	MCQ	`fit()`	`predict()`	* `score()`	* `transform()`	\N	A	A: True\nB: This is used *after* fitting; to make predictions.\nC: This returns the *score* (e.g. $R^2$ or RMSE) on a new dataset, after fitting has been done.\nD: This is also only called *after* fitting: to transform a dataset, e.g. scaling, PCA, etc. 	1.0	low	Supervised Learning, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
125	73	1	\N	5	\N	Given a feature matrix `X` of shape $100 \\times 5$, what is the shape of the corresponding label vector `y`?	MCQ	(1,5)	(100,1)	(100,)	(5,1) 	\N	C	\N	1.0	low	Data Manipulation, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
126	73	1	\N	6	\N	What is the output of the following code snippet?\n\n```{python eval=FALSE}\nfrom sklearn.metrics import accuracy_score\n\ny_true = [1, 0, 1, 1, 0]\ny_pred = [1, 0, 0, 1, 1]\nprint(accuracy_score(y_true, y_pred))\n```	MCQ	0.2	There will be an error message because no model has been fitted.	0.4	0.6	\N	D	A Incorrect.\nB The function only requires a `ytrue` and a `ypred` array. It will still run as per normal.\nC Incorrect.\nD Correct - accuracy is the number of correct predictions (3) divided by the number of \n  total predictions made (5).	1.0	med	Model Validation, Supervised Learning, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
127	73	1	\N	7	\N	Which of the following scikit-learn models is/are typically used for regression problems (not classification)?	MRQ	Decision Tree Regression	 Logistic Regression	Linear Regression	Naive Bayes	\N	A, C	A Correct\nB This is a model for performing binary classification.\nC Correct.\nD This is used for classification.	1.0	low	Supervised Learning,Regression	2025-10-22 05:47:27.159819	\N	1	\N
128	73	1	1	8	\N	Consider a new wine with the following features, but unknown `type`. \n```{python, echo=FALSE}\nwine2.sample(n=1, random_state=2002).iloc[:, 0:11].T\n```\n\nApply the decision tree rules to the above features to estimate the probability that the wine is *white*.	MCQ	0.995	0.005	0.01	0.99	\N	B	The correct leaf is the eighth from the left. Note that darker blue indicates higher probability of red, and darker orange indicates higher probability of white. In the terminal node, there are 5 instances of white and 987 instances of red. Hence the estimated probability is 5/(987 + 5) = 0.005.\n\nA is the estimated probability of red.\nB Correct\nC Incorrect - uses gini, which is not probability.\nD Incorrect - uses gini, which is not probability.	1.0	med	Supervised Learning, Decision Tree, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
142	1	10	13	1	12	Use the train set with three standardized features to form the KNN classiers where k = 3, 5, 7, 9, 11, and accuracy value for each classier is kept in a vector named accuracy.	Code	\N	\N	\N	\N	\N	library(class)\n\nK = c(3, 5, 7, 9, 11) \n# length(K) = 5\n\naccuracy= numeric()\n \nfor (i in K){ \n\n\tpred <- knn(train=train.X, test=test.X, cl=train.Y, k=i) \n\t# KNN with k receiving value as in vector K\n\n      confusion.matrix = table(test.Y, pred)  \n      \n      accuracy =append(accuracy, sum(diag(confusion.matrix))/sum(confusion.matrix) )\n      }	\N	6	high	Supervised Learning, KNN, Model Validation, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
129	73	1	1	9	\N	Consider a new wine with the following features, but unknown `type`. \n```{python, echo=FALSE}\nwine2.sample(n=1, random_state=22).iloc[:, 0:11].T\n```\n\nApply the decision tree rules to the above features to estimate the probability that the wine is *red*.	MCQ	0.008	0.992	0.016	0.984	\N	A	The correct leaf is the eighth from the right. Note that darker blue indicates \nhigher probability of red, and darker orange indicates higher probability of \nwhite. In the terminal node, there are 3617 instances of white and 30 instances \nof red. Hence the estimated probability is 30/(30+3617) = 0.008.\n\nA Correct\nB This is the estimated probability of white.\nC Incorrect - uses gini, which is not probability.\nD Incorrect - uses gini, which is not probability.	1.0	med	Supervised Learning, Decision Tree, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
130	73	1	2	10	\N	Compute the following metrics for **white wine** category, to 3 d.p.:\n\n* precision: ______(1)______\n* recall:    ______(2)______\n* accuracy:  ______(3)______	SRQ	\N	\N	\N	\N	\N	1. 0.985,\n2. 0.997\n3. 0.987	1. 3908/(3908+60) = 0.985\n2. 3908/(3908+10) = 0.997\n3. (3908+1219)/(5197) = 0.987	1.0	med	Supervised Learning, Decision Trees, Model Validation, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
131	1	10	13	1	1	Write code to change the name of the 4th column of data to Surgical.	Code	\N	\N	\N	\N	\N	names(data)[4] = "Surgical" \nnames(data)	\N	2	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
132	1	10	13	1	2	Write code to create a table of proportions for column Surgical. Report the percentage of patients that had surgery.	Code	\N	\N	\N	\N	\N	# table(data$Surgical) # RAW FREQUENCY: 14 patient got Surgical\nprop.table(table(data$Surgical))*100 # PERCENTAGE TABLE \n# 56% of patients had surgery \n\nattach(data)	\N	2	low	Data Manipulation, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
133	1	10	13	1	3	Write code to create a histogram with normal density curve overlay-ed for the sample of satisfaction.	Code	\N	\N	\N	\N	\N	hist(Satisfaction, freq = FALSE) \nn = length(Satisfaction)\n\nhist(Satisfaction, freq=FALSE, main = paste("Histogram of Total Sales"),\n     xlab = "total sales", ylab="Probability", \n     col = "grey")#, ylim = c(0, 0.002))\nx <- seq(0, max(Satisfaction), length.out=n)\ny <- dnorm(x, mean(Satisfaction), sd(Satisfaction))\nlines(x, y, col = "red") # this is the normal density curve \n	\N	2	low	Data Manipulation, EDA	2025-10-22 05:47:27.159819	\N	1	\N
134	1	10	13	1	4	Write code to create a QQ plot for the sample of satisfaction. Give your comments.	Code	\N	\N	\N	\N	\N	qqnorm(Satisfaction, pch = 20)\nqqline(Satisfaction, col = "red") \n\n# COMMENTS: BOTH LEFT TAIL AND RIGHT TAIL ARE NOT CLEARLY CONTRADICT FROM NORMAL \n# SOME MIGHT SAY: RIGHT TAIL POSSIBLY/LIGHTLY SHORTER THAN NORMAL	\N	2	low	Data Manipulation, EDA, Basic Concepts in Statistics\t	2025-10-22 05:47:27.159819	\N	1	\N
135	1	10	13	1	5	Write code to create box plots of the satisfaction scores by groups of surgical status. Give your comments.	Code	\N	\N	\N	\N	\N	boxplot(Satisfaction ~ Surgical) \n# the median point of satisfaction for patients got surgical is lower.\n# 2 boxes are overlapping. \n# Hence, NO clear difference in the satisfaction points of patients with or without surgical. \n# no outlier for both groups 	\N	4	med	Data Manipulation, EDA	2025-10-22 05:47:27.159819	\N	1	\N
136	1	10	13	1	6	Write code to create a scatter plot of satisfaction score against the age of patients for which the points are classied by the surgical status: points of patients had surgical is in red color and points of patients with no surgical is in blue color. Give your comments.	Code	\N	\N	\N	\N	\N	plot(Satisfaction ~ Age, type = "n")\npoints(Satisfaction[which(Surgical == 1)] ~ Age[which(Surgical==1)], col = "red", pch = 20)\npoints(Satisfaction[which(Surgical == 0)] ~ Age[which(Surgical==0)], col = "blue", pch = 20)\nlegend(25, 50, legend = c("Surgical", "No surgical"), col = c("red","blue"), pch=c(20,20))\n\n\ncor(Satisfaction, Age) # -0.87\n# strong negative association, quite linear  \n# the variablity of satisfaction is quite stable when age changes 	\N	6	med	Data Manipulation, EDA	2025-10-22 05:47:27.159819	\N	1	\N
137	1	10	13	1	7	Fit a linear regression model for the response variable Satisfaction, named as M, using all input features, Age, Severity, Surgical and Anxiety. Report p-values of the regressors that are NOT signicant in the model, at signicance level 0.1.	Code	\N	\N	\N	\N	\N	data$Surgical = as.factor(data$Surgical) # \n\nM = lm(Satisfaction ~ Age + Severity + Surgical + Anxiety, data = data) \n\nsummary(M)\n\n# variable that is the most non-significant is Surgical with p-value 0.5968 	\N	4	med	Linear Modeling, Model Validation, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
138	1	10	13	1	8	Two patients, A and B, that have information listed below. Write code to predict the satisfaction score for both of them. Report the prediction values.\nA: Age = 35, Severity = 45, Anxiety = 2.5 , and had no surgical.\nB: Age = 60, Severity = 40, Anxiety = 3 , and had surgical.	Code	\N	\N	\N	\N	\N	new = data.frame(Age = c(35, 60), Severity = c(45, 40), Surgical = c("0", "1"), Anxiety = c(2.5, 3))  \n\npredict(M, newdata = new) \n\n# REPORT THE OUTCOMES\n# A: 82.19378 \n# B: 58.83136	\N	4	med	Linear Modeling, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
139	1	10	13	1	9	Write R code to create a new column in data, names as S where S has two categories: Good and Not Good. \nS is Good if the satisfaction score in Satisfaction is larger than 70; and S is Not Good if the satisfaction score in Satisfaction is ≤ 70.	Code	\N	\N	\N	\N	\N	data$S = ifelse(data$Satisfaction >70, "Good", "Not Good")\n\nhead(data) # 6 columns	\N	2	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
140	1	10	13	1	10	Write code to create a new data frame, called data.X which has the three columns Age, Severity and Anxiety after standardization for all patients.	Code	\N	\N	\N	\N	\N	data.X = scale(data[, c(2,3,5)]) # scale Age, Severity and Anxiety	\N	2	low	Data Manipulation, Unsupervised Learning	2025-10-22 05:47:27.159819	\N	1	\N
141	1	10	13	1	11	Write code to randomly split the total patients into two groups: one group has 15 patients (will be the train set) and other group has the rest of patients (will be the test set).\nFor the questions below, we consider S as the response variable. We would want to form KNN classiers using input features Age, Severity and Anxiety which helps to predict if a patient ranks Good or Not Good when the patient discharges from the hospital.	Code	\N	\N	\N	\N	\N	n1 = 15 # number of points in train set\n\nn2 = 10 # number of points in test set\n\nlabel = c(rep(1, n1), rep(2, n2))  # this has length of 25  \n# create n1 number 1 and n2 number 2, to use them as labels\n# label 1 is for train set; label 2 is for test set.\n# we'll assign the labels to each row randomly\n\nlabel = sample(label) \n# we mix well the labels with each other in a random order\n\ntest.row <- which(label == 2) \n# get the index of the points that will be in the test set\ntest.X = data.X[test.row, ]\ntest.Y = data[test.row, 6]\n\ntrain.X = data.X[-test.row, ]\ntrain.Y = data[-test.row, 6]\n\n\n\ncbind(test.X, test.Y) # for reference \ncbind(train.X, train.Y) # for reference \n\n### NOTE: STUDENT MIGHT HAVE DIFFERENT WAYS TO RANDOMLY SPLIT 25 POINTS INTO TRAIN AND TEST. \n# PLEASE CHECK CAREFULLY AND AWARD THE POINTS IF THEY DO IT CORRECTLY.\n\n	\N	4	med	Data Manipulation, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
143	1	10	13	1	13	Write code to plot accuracy against k in the question above.	Code	\N	\N	\N	\N	\N	accuracy\n# [1] 0.8 0.9 0.8 1.0 0.8\n\nplot(K, accuracy, xlab = "k", ylab = "Accuracy", pch = 20, col = "red", type = "l")	\N	2	low	Supervised Learning , KNN, EDA, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
144	1	10	13	1	14	Using accuracy as the criterion, report the best k found and the accuracy of the KNN classier with that value of k.	Code	\N	\N	\N	\N	\N	cbind(K, accuracy) \n# this helps to check which value of k gives highest accuracy\n\n# Report: k = 9 is the best	\N	2	low	Supervised Learning, KNN, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
145	1	10	13	1	15	Use the KNN with the best k found in Question 14 to predict the rank (Good, Not Good ) that patient A listed in Question 8 will evaluates the hospital service.\nHint: you can use the same train set as in Question 12 above. You may standardize the values for the new patient using the mean and the standard deviation of all the patients in the data set given.	Code	\N	\N	\N	\N	\N	# GET THE MEAN AND SD OF EACH COLUMN IN data[, c(2,3,5)] SO THAT WE CAN STANDARDIZE NEW POINTS - patient A\n\nnew  # this is for two patients A and B THAT WAS FORMED IN LINEAR MODEL\n\nmean = colMeans(data[, c(2,3,5)]) \n# mean from orignal data, before standardization\n# Age Severity  Anxiety \n# 50.840   45.920    3.932 \n\nsd = apply(X = data[, c(2,3,5)], FUN = sd, MARGIN  = 2) \n# Age  Severity   Anxiety \n# 14.809006 13.028558  1.764162 \n\n# Standardize patient A: 1st row, columns 1, 2, 4 only (not taking column 3 = Surgical)\n\nscale.A = (new[1,c(1,2,4)] - mean)/sd \n\n# ANOTHER WAY IS TO FIND THE MEAN AND SD FOR EACH COLUMN SEPARATELY\n\n# THEN you can scale one value at a time for patient A (row 1 of "new")\nAge.A = ( new[1, 1] - mean(data$Age)  ) /(sd(data$Age))\nSeverity.A = ( new[1, 2] - mean(data$Severity)  ) /(sd(data$Severity)) \nAnxiety.A = ( new[1, 4] - mean(data$Anxiety)  ) /(sd(data$Anxiety)) \n\nnew.scale.A = data.frame(Age = Age.A, Severity = Severity.A, Anxiety = Anxiety.A)\n# new.scale.A IS EXACTLY THE SAME AS scale.A\n\n\n# APPLY KNN with k = 9, TO PREDICT THE RESPONSE FOR patient A:\nknn(train=train.X, test=scale.A, cl=train.Y, k=9) \n\n# REPORT: PATIENT A is predicted as will rank Good for for hospital service. 	\N	6	high	Supervised Learning, KNN, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
146	1	10	14	2	1	Define a function, function.year, which helps to calculate and return the number of years that Alena Lee could save up enough money if the proportion of annual salary she puts for savings is fixed at 0.2 (20%).	Code	\N	\N	\N	\N	\N	rate = 0.05 # rate of salary increasing yearly\n\nsaved = 30000 \nyear = 0\nfunction.year = function(salary, portion_save = 0.2){\n\twhile(saved <100000 ) {\n\t\tsalary = salary*(1 + rate) # MUST INCREASE AT THE START \n\t\tyear = year + 1\n\t\tsaved = saved + portion_save *salary\n\n\t\t#print(c(saved, salary) )\n\t}\n\treturn(year)\n}\n\nfunction.year(salary = 50000) \n# this means if Alena Lee saves 20% of her annual salary, then she needs 6 years to get saved >=100k	\N	5	high	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
147	1	10	14	2	2	Using function function.year defined above, write R codes that help to calculate the smallest proportion of annual salary that she should save so that she could have enough money for her start-up at the end of 2029, (5 years counting from start of 2025 to end of 2029).	Code	\N	\N	\N	\N	\N	################# FIRST METHOD: USE WHILE LOOP AND THE FUNCTION DEFINED ABOVE\n\nF = function(salary){\n\t\nportion= seq(0.01, 1, by = 0.01) \nyear = 6\ni= 1\nwhile( (year >5) & (i <=100) ){\n\tsaved = 30000\n\tyear = 0\n\tportion_save = portion[i] # we need this for the return/output of the function\n\tyear = function.year(salary, portion_save = portion[i])\n\tif (year >5) {i = i+ 1}\n}\nreturn(portion_save)\n\n}\n\nF(salary = 50000) # 0.25\n\n# That means, to have enough 100k in 5 years, \n# she needs to save at least 25% of the salary\n\n\n############# SECOND METHOD: USE FOR LOOP FOR ALL THE POSSIBLE PROPORTIONS: 0.01 TO 1.00\n# AND USE FUNCTION DEFINED ABOVE TO CALCULATE NUMBER OF YEARS\n\n# idea: we'll try for each value of proportion, starting from 0.01 -> 0.02 -> 0.03..., till 0.99 and 1\n# to see how many years it takes to get the saved value be >=100k.\n# the smallest proportion that helps to save enough money in 5 years is chosen.\n# the variable i of the for loop will run through the indexes of vector "portion", from 1 to 100\n\nnumber.year = numeric() \n\nportion= seq(0.01, 1, by = 0.01) \n\nfor (i in 1:100) {\n\tportion_save = portion[i]\n\tsaved = 30000\n\tyear = 0\n\tyear = function.year(salary = 50000, portion_save = portion[i])\n\tnumber.year = append(number.year, year)\n\ti = i + 1\t\n}\n\ncbind(portion, number.year)\n# this matrix list the number of years to get saved value >=100k (2nd col), for \n# each value of proportion (in 1st col)\n# it shows that when proportion = 0.25 or larger, the number of years to get \n# saved value be >=100 is 5 years or less than 5 years.	\N	5	high	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
148	1	8	8	1	\N	In order to use K-Means algorithm for a data set, we need to identify the response column in that data set first, then apply function kmeans() for the response column. True or False?	T/F	True	False	\N	\N	\N	B	K-Means is an algorithm for unsupervised learning, where there is no response for the ‘model’ to learn. 	1.0	low	Unsupervised Learning, K Means	2025-10-22 05:47:27.159819	\N	1	\N
149	1	8	8	2	\N	The number of clusters (or groups) for all the flats in the data set given could be chosen differently from user to user. True or False?	T/F	True	False	\N	\N	\N	A	One might choose 2, other might choose 3 or 4, etc.	1.0	low	Unsupervised Learning, K Means	2025-10-22 05:47:27.159819	\N	1	\N
150	1	8	8	3	\N	Clustering by K-Means algorithm should only be used for quantitative variables. True or False?	T/F	True	False	\N	\N	\N	A	the algorithm calculates the Euclidian distance between the data points, hence, it should only be used for quantitative variable, not for categorical variable, especially nominal ones.	1.0	low	Unsupervised Learning, Data Manipulation, K Means	2025-10-22 05:47:27.159819	\N	1	\N
151	1	8	8	4	\N	We could check the goodness of fit of the K-Means algorithm for the data set given above, for example, by calculating the accuracy of it. True or False?	T/F	True	False	\N	\N	\N	B	There is no response in that data set, and there is no real cluster for those flats. Hence, the clustering by the algorithm is just to separate those flats into different groups, and there is no confirmation for the clustering be right or wrong.	1.0	low	Unsupervised Learning, Model Validation, K Means	2025-10-22 05:47:27.159819	\N	1	\N
152	1	8	8	5	\N	In order to decide on the number of clusters for a data set, the plot below could help	MCQ	Box plot of each column	Histogram of each column	Scatter plot of every two quantitative columns	Pie chart of every column	\N	C	\N	1.0	low	Unsupervised Learning, Data Manipulation, K Means	2025-10-22 05:47:27.159819	\N	1	\N
153	1	8	8	6	\N	If the quantitative variables in the data set are of very different magnitudes, we should standardize each of them before applying the K-Means algorithm. True or False?	T/F	True	False	\N	\N	\N	A	This is because the algorithm calculates the Euclidian distance between data points. Hence, the variable with large magnitude will dominate the distance. That means, the clustering will mainly be affected by that variable and the contribution of variable (s) with small magnitude will become minor in clustering step.	1.0	low	Unsupervised Learning, Data Manipulation, K Means	2025-10-22 05:47:27.159819	\N	1	\N
162	1	6	5	2	\N	What is the object “prediction” defined by the code in line 20?	MCQ	The real outcome for data points in the test set, based on KNN classifier with k = 5.	The predicted outcome for data points in the original data set, on KNN classifier with k = 5.	The predicted outcome for data points in the train set, on KNN classifier with k = 5.	The predicted outcome for data points in the test set, based on KNN classifier with k = 5.	\N	D	\N	1.0	low	Supervised Learning, KNN	2025-10-22 05:47:27.159819	\N	1	\N
154	73	11	\N	3	\N	In which of the following situations is simulation modeling appropriate?	MCQ	A company wants to understand if a customer will churn (i.e. take his/her business elsewhere), using historical customer behavior.	A hospital is exploring the impact of different staffing levels on wait times in the emergency room during peak hours.	A retail chain wants to identify subsets of customers based on purchasing patterns, in order to offer more personalized marketing strategies to these groups.	A company is assessing how different weather patterns might affect delivery times with the aim to adjust their shipping/routing strategies accordingly.	\N	B, D	A Incorrect: Supervised learning.\nB Correct: Simulation modeling (exploring staffing levels and their impact on wait times).\nC Incorrect: Unsupervised learning (grouping customers based on purchasing patterns without labels).\nD Correct: Simulation modeling (assessing how weather affects delivery times).	1.0	low	Simulation Modeling, Supervised Learning, Unsupervised Learning	2025-10-22 05:47:27.159819	\N	1	\N
155	73	11	\N	4	\N	An analyst working for a ride-sharing company wants to estimate the average waiting time for passengers during peak hours. The analyst intends to use simulation modeling to understand how different factors such as the number of available drivers, traffic conditions, and demand for rides, affect waiting times over the course of a week.\n\nAs the analyst *prepares to run this simulation*, what **specific** data should they collect to calibrate the model accurately? 	SRQ	\N	\N	\N	\N	\N	Here are some possible suggestions:\n\n1. Passenger demand during peak hours (e.g., number of ride requests per hour).\n2. Number of drivers available during peak hours.\n3. Traffic condition data during peak hours (e.g., average speed or congestion levels).\n4. Average time it takes for drivers to reach passengers based on different \n   locations in the city.\n5. Variability in response times due to weather conditions or special events.\n6. Cancellation rates (both passenger and driver).	\N	1.0	med	Simulation Modeling, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
156	73	11	\N	5	\N	An analyst at an airline company wishes to estimate how often passengers will need to wait for available check-in counters during peak travel seasons. The analyst plans to run a simulation to understand the relationship between the number of open counters, the passenger arrival rate, and the average time each passenger spends at the counter.\n\nWhat data should the analyst collect before implementing the solution?	SRQ	\N	\N	\N	\N	\N	Here are some possible suggestions:\n\n1. Passenger arrival rates during peak travel times (e.g., how many passengers arrive per hour).\n2. Number of check-in counters open at different times of day. \n3. Average time a passenger spends at the counter (e.g., check-in process time).\n4. Variations due to different passenger types (e.g., business, economy, families).	\N	1.0	med	Simulation Modeling, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
157	73	11	\N	6	\N	A healthcare analyst wants to estimate the average time patients spend in the emergency room before being seen by a doctor. The analyst plans to simulate patient flow to understand how the number of doctors on duty, patient arrival rates, and the complexity of each case impact wait times.\n\nWhat data should the analyst collect before implementing the solution?	SRQ	\N	\N	\N	\N	\N	Here are some possible suggestions:\n\n1. Patient arrival rates at the emergency room during different times of day and week.\n2. Number of doctors available during various shifts.\n3. Average time doctors spend with each patient, based on case complexity.\n4. Patient triage data to understand the severity of cases and how it affects processing time.\n5. Time patients spend in other stages of the ER (e.g., registration, initial evaluation).\n6. Any seasonal factors (e.g., flu season) or special events that impact patient arrival rates.	\N	1.0	med	Simulation Modeling, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
158	73	11	\N	7	\N	A clinic takes on bookings and allocates patients to therapists according to a schedule. However, sometimes a patient cancels on short notice. The clinic would\nlike to figure out an optimal strategy that maintains a high utilisation rate of therapists, while affording them decent breaks and rest time, and a short waiting time for patients. What data would you collect prior to the modeling, and what metrics would you extract using the data collector?	SRQ	\N	\N	\N	\N	\N	Data to Collect:\n\n1. Historical Booking Data:\n    Number of patient bookings per day and per therapist.\n    Time slots allocated for each patient session.\n    Frequency and timing of last-minute cancellations (e.g., within 24 hours or less).\n    No-show rates for patients.\n\n2. Therapist Availability and Schedule:\n    Daily and weekly work schedules for each therapist.\n    Therapist preferences or limits on the number of sessions they can handle per day or week.\n    Duration of therapist breaks between sessions.\n\n3. Patient Data:\n    Average waiting time for patients between booking and the actual appointment.\n    Frequency of rescheduling by patients due to therapist unavailability.\n    Specific patient preferences for therapists (if any).\n\n4. Session Duration and Types:\n    Average duration of therapy sessions by type (e.g., physical therapy, counseling).\n    Variability in session lengths (e.g., some sessions running longer or shorter than expected).\n\n5. Cancellation Patterns:\n    Patterns of cancellation across days of the week, times of day, or specific patients.\n    The reasons provided for cancellations.\n\n6. Therapist Utilization:\n    Number of sessions per therapist each day/week.\n    Idle time between sessions for each therapist.\n    Therapist satisfaction data, if available (to understand the impact of utilization on well-being).\n\nMetrics to Extract:\n\n1. Utilization Rate of Therapists:\n    Percentage of available therapist hours that are used for patient appointments.\n    Time spent by therapists on breaks versus time spent with patients.\n\n2. Cancellation Impact:\n    Frequency of last-minute cancellations and the resulting impact on the therapist's schedule.\n    Time lost to cancellations (e.g., idle time that could not be rebooked).\n    Proportion of canceled slots that are successfully reallocated to other patients.\n\n3. Patient Waiting Time:\n    Average time patients wait between booking and appointment.\n    Variability in patient waiting times depending on cancellation or therapist availability.\n\n4. Therapist Breaks and Rest Time:\n    Average time therapists spend on breaks during a typical workday.\n    Distribution of break time across the day (e.g., short breaks between sessions versus longer midday breaks).\n    The ratio of rest time to session time to ensure therapists have enough downtime.\n\n5. Patient Satisfaction and Session Completion:\n    How cancellation rates and rescheduling affect patient satisfaction or follow-up appointments.\n    Completion rates for patient therapy plans, factoring in cancellations and reschedules.	\N	1.0	high	Simulation Modeling, Data Manipulation, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
159	73	11	\N	8	\N	In Python, the following commands can be used to initialise the random number\ngenerator. Assess if the following statement is true or false.\n\nRandom variables *cannot* be generated in Python without explicitly setting the\nseed.\n\n```\nfrom numpy.random import default_rng\nrng = default_rng(5003)\n```	T/F	True	False	\N	\N	\N	The statement is incorrect. We can always jump straight into generation  without setting the seed; Python will use a function of the timestamp to  set the seed.	\N	1.0	low	Simulation Modeling, Data Manipulation, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
160	73	11	\N	10	\N	Which of the following is a discrete random variable? 	MCQ	The amount of rainfall in a given day.  	The number of coin tosses until we observe heads.  	The time taken for a car to travel between two cities.  	The height of a randomly chosen student. 	\N	B	A Continuous\nB will be an integer count, so it is discrete. It could be a very very large number though!\nC is a variable that could be recorded with infinite precision. It is continuous.\nD is also continuous.	1.0	low	Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
161	1	6	5	1	\N	Is the train set and the test set are selected randomly from the original data set?	MCQ	Yes	No	\N	\N	\N	B	The train set is selected which includes all the data point in Year 2002 to Year 2004; while the test set include the data points in Year 2005.\nNote: In this code, the original dataset was NOT split randomly. For this code, we focus more on how the algorithm of KNN works. The part on how to split the data randomly is detailed in the later part. 	1.0	low	Supervised Learning, Data Manipulation, KNN	2025-10-22 05:47:27.159819	\N	1	\N
163	1	6	5	3	\N	Object “confusion.matrix.1” created by the code in line 22 helps to check the goodness of fit of the KNN classifier with k = 5 on	MCQ	Test data set	Train data set	Original data set (whole)	\N	\N	A	The code to form “prediction” is: knn(train[,X], test[,X], train[,Y],k=5)\nWhich wants to predict the outcome for test set.\nThe code in line 22: confusion.matrix.1 = table(prediction, test[ , Y])\nIs to form a table for the predicted outcome (prediction) and the real outcome of the test set, test[ , Y].	1.0	low	Supervised Learning, Model Validation, KNN	2025-10-22 05:47:27.159819	\N	1	\N
164	1	6	5	4	\N	Object “pred” is formed using the code in line 24. What is the length of “pred”?	SRQ	\N	\N	\N	\N	\N	1250	The classifier here uses the train set as the original data set, knn(market[,X], market[,X], market[,Y], k=5)\nAnd the test set is also the original data set, knn(market[,X], market[,X], market[,Y], k=5)\nSo, the prediction of outcome is for the test set with 1250 points.	1.0	low	Supervised Learning, KNN	2025-10-22 05:47:27.159819	\N	1	\N
165	1	6	5	5	\N	The train set and the test set used to form the KNN classifier in “pred” are the same which is all the data points given in the original data set. True or False?	T/F	True	False	\N	\N	\N	A	\N	1.0	low	Supervised Learning, Data Manipulation, KNN	2025-10-22 05:47:27.159819	\N	1	\N
166	1	6	6	6	\N	From the R code given, the three groups are formed randomly. True or False?	T/F	True	False	\N	\N	\N	A	There should be 3 groups, labeled as 1, 2, and 3.\nEach name should be matched randomly to a label. Each label should have 3 names.\nVector <y> is a vector that has labels and it has been mixed up well by the function sample().\nFor example:\nIf vector y is: 3   1   1   2   2   3   3   2   1\nthen the 1st name A should be in group 3\nthe 2nd name B should be in group 1\nthe 3rd name C should be in group 1\nThe 4th name D should be in group 2\n...\nThe 9th name I should be in group 1.	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
167	1	6	6	7	\N	Ms Pham runs this part of code for the first time and got students D and E for group 1, B and C for group 2, A and F for group 3. However, Valerie Lim also runs the same code, but she got different list as: B and C for group 1; A and D for group 2; E and F for group 3. \nIt is impossible for Ms Pham and Valerie Lim to get different answers when they run the same code above. True or False?	T/F	True	False	\N	\N	\N	B	It is possible for two of them to get different answers. This is due to the sample() function in line 30.\nLine 28 helps to form a set of group labels. 9 students, each one has a group label, 1 or 2 or 3. \nLine 30 helps to mix the labels well, not in any order. \nLine 34 help to assign students to group 1. Similarly, line 36 and 38 helps to assign students to group 2 and 3, respectively. 	1.0	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
168	1	14	16	1	\N	How many coefficients that the correct model with 3 variables (weight, width and color) should have (including the intercept)?	MCQ	4	5	6	7	\N	C	Intercept + 1 for weight + 1 for width + 3 for color (because color is categorical) = 6	1.0	low	Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
169	1	14	16	2	\N	R code is given in the photo below. How many coefficients does model M1 created from this code have?	MCQ	4	5	6	7	\N	A	Because column “color” inside data frame “crab” is still recognized by R as a numeric column by the code at line 8. In line 10, as.factor() is used, but it is to create a vector called “color” – be a categorical, but this vector is NOT inside data frame “crab”. \nModel M1 is fitted in line 12 uses column “color” inside data frame “crab” which is still numeric.	1.0	low	Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
170	1	14	16	3	\N	In the R code given, how many coefficients does model M2 have? 	MCQ	4	5	6	7	\N	C	R code for model M2 in line 12 doesn’t specify the data frame where the variables come from. Hence, R will use satell, width and weight from data frame “crab” since the command attach(crab) was run, hence R knows what satell, width and weight are. For color, after attach(crab), R updates that “color” is categorical from the code in line 10.	1.0	low	Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
171	1	14	16	4	\N	The coefficient table from the summary output of model M2 and model M3 will be the same. True or False?	T/F	True	False	\N	\N	\N	A	The R code in line 16 has declared with R that column “color” inside data frame “crab” is categorical, hence, when fitting M3 with “data = crab” in line 18, R will have 3 coefficients for color. \nIt’s recommended to fit a linear model as M3.	1.0	low	Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
172	1	14	16	5	\N	What is the output of the code at line 20, <predict(M3)>?	MRQ	The fitted values of model M3.	The predicted values of satell from model M3, for all the crabs in the data set.	The real values of response for the crabs in the data set.	\N	\N	A.B	\N	1.0	low	Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
173	1	14	16	6	\N	To get the predicted response values using model M3, for all the crabs given in the data set, we use R code in line 22, <M3$fitted.values>. True or False?	T/F	True	False	\N	\N	\N	A	\N	1.0	low	Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
174	1	14	16	7	\N	Using model M3 to predict the number of satell for a new crab with color = 4, width = 26 cm, weight = 2.6 kg. The code is given in lines 24 and 26. The code is correct. True or False?	T/F	True	False	\N	\N	\N	B	Model M3 has color as categorical, hence when creating a new crab, we need to specify color as categorical, by putting the number inside a quote sign, such as:\nnew.crab = data.frame(weight = 2.6, width = 26, color = “4”)\npredict(M3, newdata = new.crab)\nshould predict the number of satellites for the new crab.	1.0	low	Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
175	1	14	16	8	\N	A simple model M4 is fitted where the number of satellites only depends on the weight. \nAfter that, using model M4 to predict the response for the new crab with weight = 2.6 kg. R code is given below. The code is correct. True or False?	T/F	True	False	\N	\N	\N	B	From the code in line 28, we told R that model M4 is built with the values for “weight” that must be from a column inside a data frame called “crab”, specified by crab$weight. \nHence, when we use model M4 to predict for a new data point where this new one has “weight” from a data frame with the name “new” (in the line 30), R will not produce the prediction we want.\nR will just produce the prediction for the data that were used to fit the model, “crab”.\nHow to fix the issue above?\nEither we change the way to fit M4 as below, then the code will work:\nM4 = lm(satell ~ weight, data = crab) # note: do not use the form of data$y ~ data$x\nnew = data.frame(weight = 2.6)\npredict(M4, newdata = new)\n\nOR we must name the new data frame as the same as the original data frame as below.\nM4 = lm(crab$satell ~ crab$weight, data = crab) \ncrab = data.frame(weight = 2.6)\npredict(M4, newdata = crab)\nNote: this latter method is not recommended, since if we do this, we will not have the original data frame “crab” in R anymore, since it is now replaced by the new one.	1.0	low	Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
176	1	3	4	1	\N	Model M1 generated in the R code file is a 	MCQ	Linear Regression model	Logistic Regression model	Naïve Bayes model	KNN model	\N	A	Model M1 was generated by function glm(), however, family = binomial was not specified. Hence, by default settings of glm(), it will form a linear model.	1.0	low	Supervised Learning, Data Manipulation, Logistic Regression	2025-10-22 05:47:27.159819	\N	1	\N
177	1	3	4	2	\N	How many coefficients does model M2 have (including the intercept)?	MCQ	3	4	5	6	\N	C	Model M2 was generated with Churned be the response, and it depends on ALL other columns (4 columns) in the data frame “data”. Each column will need one coefficient. Hence, 4 coefficients for 4 variables with 1 intercept  5 in total.\nNote: Married is categorical with 2 categories, hence, it needs one coefficient only, not two.	1.0	low	Supervised Learning, Basic Concepts in Statistics, Logistic Regression	2025-10-22 05:47:27.159819	\N	1	\N
178	1	3	4	3	\N	Variable “Married” is NOT very significant in model M2. True or False?	T/F	True	False	\N	\N	\N	A	Its p-value is 0.33, quite large. It indicates the weak contribution of this variable in the model.	1.0	low	Supervised Learning, Model Validation, Logistic Regression	2025-10-22 05:47:27.159819	\N	1	\N
179	1	3	4	4	\N	Consider model M3. From the output of summary(M3), if we let p = prob(Churned = 1), and p-hat be the estimation of p, then we could write the fitted equation of model M3 as	MCQ	Log(p-hat) = 3.503 – 0.157*Age + 0.382*Churned_contacts	Log [ p-hat/(1-p-hat)] = 3.503 – 0.157*Age + 0.382*Churned_contacts	p-hat = 3.503 – 0.157*Age + 0.382*Churned_contacts	p = 3.503 – 0.157*Age + 0.382*Churned_contacts	p-hat / (1 – p-hat) = 3.503 – 0.157*Age + 0.382*Churned_contacts	B	\N	1.0	low	Supervised Learning, Basic Concepts in Statistics, Logistic Regression	2025-10-22 05:47:27.159819	\N	1	\N
180	1	3	4	5	\N	Consider using model M3 to predict for a customer at age 50 and have 5 churned contacts. What is the output of the R code in line 22?\npredict(M3, newdata = data.frame(Age = 50, Churned_contacts = 5), type = 'response')	MCQ	The value of Churned for that customer.	The predicted odds that the customer will churn.	The predicted probability that the customer will churn.	The predicted ratio between probability of churn and probability of not churn for that customer.	\N	C	type = ‘response’ is specified which requires R to return the probability of response = 1. That is the probability predicted by model M3.	1.0	low	Supervised Learning, Logistic Regression	2025-10-22 05:47:27.159819	\N	1	\N
181	1	3	4	6	\N	This question has one or more than one answer that is correct.\nThe coefficient -0.157 (3dp) in the summary(M3) output for variable Age means	MRQ	As Age increases by 1 unit (1 year), the probability of customer to churn will decrease by 0.157.	As Age increase by 1 unit (1 year), the log odds of customer to churn will decrease by 0.157.	As Age increase by 1 unit (1 year), the odds of customers to churn will decrease by 0.157.	As Age increase by 1 unit (1 year), the odds of customer to churn will decrease by 1.17 times.	\N	B,D	Refer to the correct answer of Q4 to get why B is correct.\nTo get an idea on why D is correct, we consider equation below.\nlog(y) = 5 * Age\nWhen Age increase by 1 then log(y) will increase by 5, hence the value of y will increase by an exponential of 5, exp(5).	1.0	low	Supervised Learning, Basic Concepts in Statistics, Logistic Regression	2025-10-22 05:47:27.159819	\N	1	\N
182	1	3	4	7	\N	When we want to fit a logistic model, the response variable could be categorical with "0" and "1" or could be numeric with 0 and 1. True or False?	T/F	True	False	\N	\N	\N	A	From the R code file, you can see that "Churned" is numeric with 0 and 1.\nglm() can fit a logistic model for this response.\nIf you change response "Churned" into categorical before fitting logistic model, it still works (you can try with the code below):\ndata$Churned = as.factor(data$Churned)  # change "Churned" into categorical, and fit model M2 \nM2<- glm(Churned ~ . , data = data, family = binomial)   # no error\nsummary(M2)  # it still works as usual.\nAn extra note: if the response variable is categorical with characters "0" and "1" then glm() can fit a logistic model for us. HOWEVER, if the response has characters like "yes" and "no", then glm() cannot fit a logistic model.	1.0	low	Supervised Learning, Data Manipulation, Logistic Regression	2025-10-22 05:47:27.159819	\N	1	\N
183	20	4	\N	1	\N	This question is to be answered using Python.\nConsider the stud_perf dataset once again. There were three measures of performance of the students:\n\n Feature\tDescription  \tDetails\n G1\t First period grade\t from 0 to 20\n G2\t Second period grade   \t from 0 to 20\n G3\t Final grade\t from 0 to 20\n\nIn this question, we shall investigate the agreement between G1 and G3 scores. If there is a high agreement, it means that teachers can drop one of the scores and still get a good estimate of final grade of a student.\n1. First, read in the dataset, and divide the G1 and G3 scores into 10 bins:\n• [0,2], (2,4], (4,6], (6,8], (8,10], (10,12], (12,14], (14,16], (16,18], (18,20]\n• You should now have two new columns G1_bin and G3_bin in the dataset.\n\n2. Next, create a contingency table with G1_bin in the rows and G3_bin in the columns.\n\n3. Convert the cell counts into proportions. The sum of entries in all cells should now equal to 1. Create a visualisation of this table of proportions that is relevant to the goal of measuring agreement.\n\n4. If we let pij be the proportion in row i and column j, then the strictest version of agreement is η0=∑i=110pii What is the range of values for η0? Which values correspond to higher agreement?\n\n5. A less stringent measure of agreement is given by η1=∑|i−j|≤1pij Compute η1 separately for the five groups defined by Medu and summarise what you observe.	Code	\N	\N	\N	\N	\N	\N	\N	8	high	Data Manipulation, EDA, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
184	20	4	\N	2	\N	In 1935, Sir R A Fisher described an experiment involving a British woman. The woman claimed that if she was presented with a cup of milk tea, she would be able to distinguish whether milk or tea was added to the cup first. To test, she was given 8 cups of tea, in four of which milk was added first.\nThe data collected was as follows:\n\n \t  Actual Milk  |  Actual  Tea\nGuessed Milk   \t3 | 1\nGuessed Tea  \t1 | 3\nSuppose that Fisher’s Exact Test was applied to assess if there was any association between her guesses and the truth. Under the null hypothesis of Fisher’s Exact Test, what is the probability of observing the table above?	MCQ	0.5	0.25	0.5625	0.228	\N	D	\N	1	high	Conditional Probability, Hypothesis Testing, Exact Test	2025-10-22 05:47:27.159819	\N	1	\N
185	20	4	\N	3	\N	Consider the following two histograms (created with Python) from the liverpool dataset used in Tutorial 2:\n!(ST2137_Questions_Figure1.png)\n\nWhat is the argument needed to convert the Histogram A into Histogram B?\nliverpool.GF.hist(    1    )	MCQ	freq=False	density=True	type="percent"	type="density" 	\N	A	\N	1	low	Data Manipulation, EDA, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
186	20	4	\N	4	\N	The data in phones.csv contains information on phone calls made in Belgium from 1950 until 1973. Let Y be the number of calls, and X be the year variable. Read the data into Python as a pandas dataframe and answer the following questions:\n\n1. Write a function that takes in three arguments: beta0, beta1, and the phones dataframe. It should compute the following L1-norm and return it: ∑i=1n|Yi−β0−β1Xi|\n\n2. Iterate over a range of beta0 and beta1 values and find the pair that minimizes the L1-norm. Return this pair of beta0 and beta1 values.\n\n3. Create a plot of this line, along with the OLS estimate, along with the datapoints.\n\n4. Discuss the benefits of the L1-fit over the OLS fit.	Code	\N	\N	\N	\N	\N	\N	\N	8	high	Regression, Optimization, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
187	20	4	\N	5	\N	Suppose that the data in liverpool_2223_season.csv has been read into Python as liverpool. The following code tabulates the goal counts for and stores them in a column in goal_counts.\ngoal_counts =pd.DataFrame(np.zeros((10, 2), dtype='int'), columns=['GF', 'GA']) \ntmp2 =liverpool.GF.value_counts() \ngoal_counts.loc[tmp2.index, 'GF'] =tmp2\nContinue the code to fill up the second column, which tabulates the goal counts against into the second column of goal_counts. Then create the following bar chart, which compares the GF and GA:\n!(ST2137_Questions_Figure2.png)	\N	\N	\N	\N	\N	\N	\N	\N	4	med	Data Manipulation, EDA, Model Validation	2025-10-22 05:47:27.159819	\N	1	\N
188	20	4	\N	6	\N	What is the most likely solution to the error below?\n!(ST2137_Questions_Figure3.png)	MCQ	The function to read the file is read.csv, not read_csv.	The pandas package has to be imported.	The pandas package has to be installed.	The separator has to be specified as sep=';'.	\N	B	\N	1	low	Data Manipulation, Debugging	2025-10-22 05:47:27.159819	\N	1	\N
189	20	4	\N	7	\N	The heifers dataset was introduced on in the topic on ANOVA. An analyst used SAS to run the ANOVA procedure and estimate the contrast comparing the Control group to the rest of the five groups. This is the code that the analyst used:\nproc glm data=ST2137.HEIFERS; \nclass type; \nmodel org=type / clparm; \nmeans type / hovtest=levene welch plots=none; \nlsmeans type / adjust=tukey pdiff alpha=.05; \nestimate 'control vs. rest' type -1 5 -1 -1 -1 -1 / divisor=5; \nrun; \nThe essential output for this particular contrast can be seen in the following figures:\n\n!(ST2137_Questions_Figure4.png)\n\nUse Python to recreate\n1.\tthe point estimate of the contrast, and\n2.\tthe confidence interval for the contrast.	Code	\N	\N	\N	\N	\N	\N	\N	6	high	Inferential Statistics, ANOVA, Data Manipulation, Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
190	20	4	\N	9	\N	What is the length of the resulting output in this Python code?\nmy_list =['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'] \nresult =my_list[2:8:2] \nlen(result)	MCQ	6	4	3	2	\N	C	\N	1	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
191	20	4	\N	11	\N	Suppose that x is a numpy array with shape (2,2) and y is a numpy array with shape (2,1). What is the name of the numpy function for adding column y as a new column to x (making it have shape (2,3))?	MCQ	np.cbind()	np.stack()	np.hstack()	np.concatenate()	\N	C	\N	1	low	Data Manipulation, NumPy	2025-10-22 05:47:27.159819	\N	1	\N
192	20	4	\N	12	\N	In many manufacturing processes, the term work-in-progress is often abbreviated to WIP. In a book manufacturing plant, WIP represents the time it takes for sheets from a press to be folded, gathered, sewn, tipped (with glue) on end sheets, and finally bound together.\nThe data set wip.txt contains samples of 20 books from each of two production plants, and the time for WIP (defined as the time in hours from when the books came off the press till they were packed in cartons).\nThere are two variables in the data set: time and plant (either 1 or 2).\nConsider the following output. For the raw data, when we construct boxplots for each plant, there is a single outlier for each plant (the maximum value in each group).\n## time \n##   count mean    std      min  25%    50%    75%    max \n## plant \n## 1 20.0  9.3820  3.997653 4.42 7.4475 8.515  11.045 21.62 \n## 2 20.0  11.3535 5.126156 2.33 8.4400 11.960 13.845 25.75\nIf we had applied a log (base e) transform to time before creating the boxplots, would these two points still be outliers? Explain your answer clearly using the summary statistics above only.	SRQ	\N	\N	\N	\N	\N	\N	\N	4	high	EDA, Basic Concepts in Statistics, Robustness	2025-10-22 05:47:27.159819	\N	1	\N
193	20	4	\N	14	\N	Using the student-mat.csv dataset from our lectures, create a contingency table from the variables address and guardian. Store it as address_guardian.\nWrite R code that will:\n1.\tCompute the proportion of students whose home address was rural, and whose guardian was their mother.\n2.\tEstimate the probability of students whose home address was rural, and whose guardian was their mother, under the null hypothesis of the chi2-test of independence.	Code	\N	\N	\N	\N	\N	\N	\N	4	med	Data Manipulation, Basic Concepts in Statistics, Conditional Probability	2025-10-22 05:47:27.159819	\N	1	\N
194	20	4	\N	15	\N	What is the length of the resulting output in this R code?\nvec1 <- c('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j') \nresult <- vec1[2:8][-2] \nlength(result)	MCQ	3	2	4	6	\N	D	\N	1	low	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
195	20	4	\N	16	\N	This question is to be answered using R.\nSuppose that daily demand for newspaper is approximately gamma distributed, with mean 10,000 and variance 1,000,000. At present, the newspaper company prints and distributes C=11,000 copies each day. The profit on each newspaper sold is $1, and the loss on each unsold newspaper is $0.25. Formally, the daily profit function h is\nh(X)={11000if X≥11000⌊X⌋+(11000−⌊X⌋)(−0.25)if X<11000\nwhere X represents the daily demand. Use simulation to estimate the expected profit per day, for various values of C. Thus recommend the optimal value of C to the company.\nEnsure that when you make your case, you include confidence intervals, and that you include a visualisation of your results to assist the company in understanding your recommendation. For this question, set your seed to be 2002.\n\nYou will be awarded more marks for\n• planning your code well,\n• for using functions such as apply instead of for loops.\n• for a clean and clear plot,\n• and for a clear explanation of your results.	Code	\N	\N	\N	\N	\N	\N	\N	6	med	Simulation Modeling, Optimization, Data Manipulation, Inference	2025-10-22 05:47:27.159819	\N	1	\N
196	20	4	\N	18	\N	After working with R, Python and SAS with one semester, you must have realised some of the strengths/limitations of these software. For each of the three software, list one advantage that you feel it has over the other two. There is no “right” or “wrong” answer, but your response should be a sincere one, and should be backed up with examples from our course material.	SRQ	\N	\N	\N	\N	\N	\N	\N	3	med	Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
197	20	4	\N	20	\N	A sequence is generated using the following recursive relation:\nxn=2xn−1−xn−2,n≥3\n where x1=0 and x2=1.\n \nWrite R code to find x30 and ∑i=130xi.	Code	\N	\N	\N	\N	\N	\N	\N	3	low	Data Manipulation, Programming Logic	2025-10-22 05:47:27.159819	\N	1	\N
198	20	4	\N	22	\N	A clinical trial is conducted to compare the efficacy of drug A and drug B on lowering blood pressure. Participants are randomly divided into two groups. One group is given drug A and the other drug B. The average reduction in blood pressure after taking the drug is measured and compared between the two groups.\nAssuming the distributional assumptions hold, the paired-sample t-test is appropriate in the above scenario (instead of the independent-sample t-test).	T/F	True	False	\N	\N	\N	B	\N	1	low	Inferential Statistics, T-tests	2025-10-22 05:47:27.159819	\N	1	\N
199	20	4	\N	23	\N	Which of the following techniques cannot be used to assess the Normality of a given dataset?	MCQ	Kolmogorov-Smirnov test	Shapiro-Wilk test	Skewness	1-sample t-test	\N	D	\N	1	low	Model Validation, EDA, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
200	20	4	\N	24	\N	In the One-Way ANOVA, we assume the following model:\nYij=μ+αi+eij,i=1,…,k,j=1,…,ni\nThe use of contr.sum( ) in R corresponds to the following constraint when performing estimation:\n•\tSetting α1=0.	T/F	True	False	\N	\N	\N	B	\N	1	med	Inferential Statistics, ANOVA, Linear Modeling	2025-10-22 05:47:27.159819	\N	1	\N
201	20	4	\N	27	\N	When assessing robustness of an estimator, one of the properties we consider is the breakdown point.\nFor a particular parameter of interest, an estimator with a large breakdown point is considered to be better than an estimator with a smaller breakdown point.	T/F	True	False	\N	\N	\N	A	\N	1	med	Basic Concepts in Statistics, Robustness	2025-10-22 05:47:27.159819	\N	1	\N
202	20	4	\N	28	\N	Consider the following SAS program:\nDATA ex_1; \nINPUT subject gender $ CA1 CA2 HW $; \nDATALINES; \n10 m 80 84 a ; \n7 m 85 89 a \n;\nWhen the code above was run, there was no output. Which one of the following two steps will fix the error?	MCQ	Removing the semi-colon on line 4.	Moving the semi-colon on line 6 to the end of line 5.	\N	\N	\N	A	\N	1	med	Data Manipulation, Programming Logic	2025-10-22 05:47:27.159819	\N	1	\N
203	20	4	\N	29	\N	Simulation can be used to estimate expected values of the form E[g(X)]=∑x=0∞g(x)p(x). The reason we can assume Normality when computing Confidence Intervals is that it is up to us to choose the number of observations to generate.	T/F	True	False	\N	\N	\N	A	\N	1	med	Simulation Modeling, Inference, Basic Concepts in Statistics	2025-10-22 05:47:27.159819	\N	1	\N
204	20	4	\N	30	\N	Suppose that X∼N(μ=0,σ2=4). Which of the following R commands will return P(X>2) ?	MCQ	pnorm(2, mean = 0, sd = 2, lower.tail = FALSE)	pnorm(2, mean = 0, var = 4, lower.tail = FALSE)	1 - qnorm(2, mean = 0, sd = 2)	1 - qnorm(2, mean = 0, var = 4)	\N	A	\N	1	low	Basic Concepts in Statistics, Data Manipulation	2025-10-22 05:47:27.159819	\N	1	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, username, password_hash) FROM stdin;
\.


--
-- Name: assessments_assessment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.assessments_assessment_id_seq', 36, true);


--
-- Name: attachments_attachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attachments_attachment_id_seq', 41, true);


--
-- Name: contexts_context_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.contexts_context_id_seq', 19, true);


--
-- Name: courses_course_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.courses_course_id_seq', 110, true);


--
-- Name: questions_question_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.questions_question_id_seq', 204, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_user_id_seq', 1, false);


--
-- Name: assessments assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_pkey PRIMARY KEY (assessment_id);


--
-- Name: attachments attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_pkey PRIMARY KEY (attachment_id);


--
-- Name: contexts contexts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contexts
    ADD CONSTRAINT contexts_pkey PRIMARY KEY (context_id);


--
-- Name: courses courses_course_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_course_code_key UNIQUE (course_code);


--
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (course_id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (question_id);


--
-- Name: attachments uq_attachments_context_file; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT uq_attachments_context_file UNIQUE (context_id, attachment_name);


--
-- Name: attachments uq_attachments_question_file; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT uq_attachments_question_file UNIQUE (question_id, attachment_name);


--
-- Name: contexts uq_contexts_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contexts
    ADD CONSTRAINT uq_contexts_key UNIQUE (assessment_id, context_local_id);


--
-- Name: questions uq_questions_dedupe; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT uq_questions_dedupe UNIQUE (course_id, assessment_id, question_text);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: idx_attachments_context_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attachments_context_id ON public.attachments USING btree (context_id);


--
-- Name: idx_attachments_question_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attachments_question_id ON public.attachments USING btree (question_id);


--
-- Name: idx_contexts_assessment_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_contexts_assessment_id ON public.contexts USING btree (assessment_id);


--
-- Name: idx_contexts_course_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_contexts_course_id ON public.contexts USING btree (course_id);


--
-- Name: idx_questions_assessment_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_assessment_id ON public.questions USING btree (assessment_id);


--
-- Name: idx_questions_context_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_context_id ON public.questions USING btree (context_id);


--
-- Name: uq_assessments_unique_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_assessments_unique_idx ON public.assessments USING btree (course_id, assessment_type, COALESCE(assessment_acadyear, ''::text), COALESCE(assessment_semester, ''::text));


--
-- Name: assessments assessments_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(course_id) ON DELETE CASCADE;


--
-- Name: assessments assessments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: attachments attachments_context_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_context_id_fkey FOREIGN KEY (context_id) REFERENCES public.contexts(context_id) ON DELETE CASCADE;


--
-- Name: attachments attachments_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(question_id) ON DELETE CASCADE;


--
-- Name: contexts contexts_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contexts
    ADD CONSTRAINT contexts_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES public.assessments(assessment_id) ON DELETE CASCADE;


--
-- Name: contexts contexts_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contexts
    ADD CONSTRAINT contexts_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(course_id) ON DELETE CASCADE;


--
-- Name: questions questions_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES public.assessments(assessment_id) ON DELETE CASCADE;


--
-- Name: questions questions_context_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_context_id_fkey FOREIGN KEY (context_id) REFERENCES public.contexts(context_id) ON DELETE SET NULL;


--
-- Name: questions questions_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(course_id) ON DELETE CASCADE;


--
-- Name: questions questions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: questions questions_previous_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_previous_version_id_fkey FOREIGN KEY (previous_version_id) REFERENCES public.questions(question_id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

\unrestrict cLXcZl7NSe9NRW6xldOA5eI3hnjcddoDIJrg667Uyjjcalv31jmSOvcyVKwl3GJ

