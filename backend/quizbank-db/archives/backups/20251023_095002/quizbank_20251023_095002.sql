--
-- PostgreSQL database dump
--

\restrict XqIqqmPNdjI1ETTydpsvRJLurltaqeG1QgfVIUaLfK8aaXCJtiJZrYz0cZMsPSc

-- Dumped from database version 13.22 (Debian 13.22-1.pgdg13+1)
-- Dumped by pg_dump version 13.22 (Debian 13.22-1.pgdg13+1)

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
    assessment_id bigint NOT NULL,
    course_id bigint NOT NULL,
    assessment_type character varying(64) NOT NULL,
    assessment_acadyear character varying(32),
    assessment_semester character varying(32),
    created_at timestamp with time zone DEFAULT now(),
    created_by bigint
);


ALTER TABLE public.assessments OWNER TO postgres;

--
-- Name: assessments_assessment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.assessments ALTER COLUMN assessment_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.assessments_assessment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: context_attachments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.context_attachments (
    context_attachment_id bigint NOT NULL,
    context_id bigint NOT NULL,
    attachment_name character varying(256) NOT NULL,
    attachment_url character varying(1024)
);


ALTER TABLE public.context_attachments OWNER TO postgres;

--
-- Name: context_attachments_context_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.context_attachments ALTER COLUMN context_attachment_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.context_attachments_context_attachment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: contexts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contexts (
    context_id bigint NOT NULL,
    assessment_id bigint NOT NULL,
    course_id bigint NOT NULL,
    context_local_id character varying(64) NOT NULL,
    context_text text NOT NULL
);


ALTER TABLE public.contexts OWNER TO postgres;

--
-- Name: contexts_context_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.contexts ALTER COLUMN context_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.contexts_context_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.courses (
    course_id bigint NOT NULL,
    course_code character varying(32) NOT NULL,
    course_name character varying(256) NOT NULL
);


ALTER TABLE public.courses OWNER TO postgres;

--
-- Name: courses_course_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.courses ALTER COLUMN course_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.courses_course_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: question_attachments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_attachments (
    question_attachment_id bigint NOT NULL,
    question_id bigint NOT NULL,
    attachment_name character varying(256) NOT NULL,
    attachment_url character varying(1024)
);


ALTER TABLE public.question_attachments OWNER TO postgres;

--
-- Name: question_attachments_question_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.question_attachments ALTER COLUMN question_attachment_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.question_attachments_question_attachment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.questions (
    question_id bigint NOT NULL,
    assessment_id bigint NOT NULL,
    course_id bigint NOT NULL,
    context_id bigint,
    question_number integer,
    sub_question_number integer,
    question_text text NOT NULL,
    question_type character varying(64),
    option_a text,
    option_b text,
    option_c text,
    option_d text,
    option_e text,
    correct_answer character varying(64),
    explanation character varying(4096),
    points numeric(4,1),
    difficulty character varying(32),
    concepts character varying(1024),
    created_by bigint,
    created_at timestamp with time zone DEFAULT now(),
    version_number integer DEFAULT 1 NOT NULL,
    previous_version_id bigint,
    original_id bigint,
    is_latest boolean DEFAULT true NOT NULL,
    CONSTRAINT chk_orig_not_self CHECK (((original_id IS NULL) OR (original_id <> question_id))),
    CONSTRAINT chk_prev_not_self CHECK (((previous_version_id IS NULL) OR (previous_version_id <> question_id)))
);


ALTER TABLE public.questions OWNER TO postgres;

--
-- Name: questions_question_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.questions ALTER COLUMN question_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.questions_question_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: system_meta; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.system_meta (
    key text NOT NULL,
    value text
);


ALTER TABLE public.system_meta OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    username character varying(128) NOT NULL,
    password_hash character varying(256) NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.users ALTER COLUMN user_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Data for Name: assessments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.assessments (assessment_id, course_id, assessment_type, assessment_acadyear, assessment_semester, created_at, created_by) FROM stdin;
1	1	Final	2425	1	2025-10-23 01:50:02.213579+00	\N
2	1	Midterm	2425	1	2025-10-23 01:50:02.213579+00	\N
3	1	Quiz1	2425	1	2025-10-23 01:50:02.213579+00	\N
4	1	Quiz2	2425	1	2025-10-23 01:50:02.213579+00	\N
5	1	Quiz3	2425	1	2025-10-23 01:50:02.213579+00	\N
6	1	Quiz4	2425	1	2025-10-23 01:50:02.213579+00	\N
7	1	Quiz5	2425	1	2025-10-23 01:50:02.213579+00	\N
8	1	Quiz6	2425	1	2025-10-23 01:50:02.213579+00	\N
9	1	Quiz7	2425	1	2025-10-23 01:50:02.213579+00	\N
10	1	Quiz8	2425	1	2025-10-23 01:50:02.213579+00	\N
11	28	Regression	\N	\N	2025-10-23 01:50:02.213579+00	\N
12	28	Simulation	\N	\N	2025-10-23 01:50:02.213579+00	\N
13	28	Supervised	\N	\N	2025-10-23 01:50:02.213579+00	\N
14	30	Quiz1	\N	\N	2025-10-23 01:50:02.213579+00	\N
15	30	Quiz2	\N	\N	2025-10-23 01:50:02.213579+00	\N
16	32	Questions	\N	\N	2025-10-23 01:50:02.213579+00	\N
17	35	Questions	\N	\N	2025-10-23 01:50:02.213579+00	\N
\.


--
-- Data for Name: context_attachments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.context_attachments (context_attachment_id, context_id, attachment_name, attachment_url) FROM stdin;
\.


--
-- Data for Name: contexts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.contexts (context_id, assessment_id, course_id, context_local_id, context_text) FROM stdin;
\.


--
-- Data for Name: courses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.courses (course_id, course_code, course_name) FROM stdin;
1	DSA1101	Introduction to Data Science
3	DSA2101	Essential Data Analytics Tools: Data Visualisation
4	DSA3101	Data Science in Practice
5	DSA3361	Inferential Data Analytics
6	DSA3362	Predictive Data Analytics
7	DSA4211	High Dimensional Statistical Analysis
8	DSA4212	Optimisation for Large‑Scale Data Driven Inference
9	DSA4213	Natural Language Processing for Data Science
10	DSA4262	Sense‑Making Case Analysis: Health and Medicine
11	DSA4263	Sense‑Making Case Analysis: Business and Commerce
12	DSA4264	Sense‑Making Case Analysis: Public Policy and Society
13	DSA4265	Sense‑Making Case Analysis: Economics
14	DSA4266	Sense‑Making Case Analysis: Science and Technology
15	DSE1101	Introductory Data Science for Economics
16	DSE3101	Practical Data Science for Economics
17	DSS5101	Principles of Sustainability
18	DSS5102	Advanced Regression and Time Series Analysis
19	DSS5103	Geospatial Data Analysis
20	DSS5104	Machine Learning and Predictive Modelling
21	DSS5105	Data Science Projects in Practice
22	DSS5201	Data Visualisation
23	DSS5202	Sustainable Systems Analysis
24	DSS5203	ESG Data for Sustainable Finance and Investments
25	DSS5210	Research/Industry Project I
26	DSS5211	Research/Industry Project II
27	HS2914	How to Teach Humans and Machines to Talk
28	IND5003	IND5003
30	ST1131	ST1131
32	ST2131	ST2131
34	ST2132	Mathematical Statistics
35	ST2137	Statistical Computing and Programming
37	ST2334	Probability and Statistics
38	ST3131	Regression Analysis
39	ST3232	Design and Analysis of Experiments
40	ST3236	Stochastic Processes I
41	ST3239	Survey Methodology
42	ST3244	Demographic Methods
43	ST3246	Statistical Models for Actuarial Science
44	ST3247	Simulation
45	ST3248	Statistical Learning I
46	ST4231	Computer Intensive Statistical Methods
47	ST4233	Linear Models
48	ST4234	Bayesian Statistics
49	ST4238	Stochastics Processes II
50	ST4245	Statistical Methods for Finance
51	ST4248	Statistical Learning II
52	ST4250	Multivariate Statistical Analysis
53	ST4253	Applied Time Series Analysis
54	ST5188	Advanced Data Science Project
55	ST5201	Statistical Foundations of Data Science
56	ST5201X	Statistical Foundations of Data Science
57	ST5202	Applied Regression Analysis
58	ST5202X	Applied Regression Analysis
59	ST5203	Design of Experiments
60	ST5207	Nonparametric Regression
61	ST5209X	Analysis of Time Series Data
62	ST5211X	Sampling from Finite Populations
63	ST5212	Survival Analysis
64	ST5213	Advanced Categorical Data Analysis
65	ST5218	Advanced Statistical Methods in Finance
66	ST5221	Stochastic Processes and Applications
67	ST5225	Statistical Analysis of Networks
68	ST5226	Spatial Statistics
69	ST5227	Applied Statistical Learning
70	ST5229	Deep Learning in Data Analytics
71	ST5230	Applied Natural Language Processing
72	ST5290	Data Science Industry Project
73	ST6101	Advanced Statistical Theory
74	ST6102	Advanced Statistical Theory II
75	ST6103	Advanced Probability Theory
76	ST6104	Statistical Models
77	ST6105	Computational Statistics
78	ST6120	Graduate Seminar Module
79	ST6241	Topics I
\.


--
-- Data for Name: question_attachments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.question_attachments (question_attachment_id, question_id, attachment_name, attachment_url) FROM stdin;
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.questions (question_id, assessment_id, course_id, context_id, question_number, sub_question_number, question_text, question_type, option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, points, difficulty, concepts, created_by, created_at, version_number, previous_version_id, original_id, is_latest) FROM stdin;
\.


--
-- Data for Name: system_meta; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.system_meta (key, value) FROM stdin;
seeded_by_python	2025-10-23 01:50:02.225917+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, username, password_hash) FROM stdin;
\.


--
-- Name: assessments_assessment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.assessments_assessment_id_seq', 17, true);


--
-- Name: context_attachments_context_attachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.context_attachments_context_attachment_id_seq', 1, false);


--
-- Name: contexts_context_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.contexts_context_id_seq', 1, false);


--
-- Name: courses_course_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.courses_course_id_seq', 79, true);


--
-- Name: question_attachments_question_attachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.question_attachments_question_attachment_id_seq', 1, false);


--
-- Name: questions_question_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.questions_question_id_seq', 1, false);


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
-- Name: context_attachments context_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.context_attachments
    ADD CONSTRAINT context_attachments_pkey PRIMARY KEY (context_attachment_id);


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
-- Name: question_attachments question_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_attachments
    ADD CONSTRAINT question_attachments_pkey PRIMARY KEY (question_attachment_id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (question_id);


--
-- Name: system_meta system_meta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_meta
    ADD CONSTRAINT system_meta_pkey PRIMARY KEY (key);


--
-- Name: assessments uq_assessment; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT uq_assessment UNIQUE (course_id, assessment_type, assessment_acadyear, assessment_semester);


--
-- Name: contexts uq_context; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contexts
    ADD CONSTRAINT uq_context UNIQUE (assessment_id, context_local_id);


--
-- Name: context_attachments uq_context_attachment; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.context_attachments
    ADD CONSTRAINT uq_context_attachment UNIQUE (context_id, attachment_name);


--
-- Name: questions uq_question; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT uq_question UNIQUE (course_id, assessment_id, question_text);


--
-- Name: question_attachments uq_question_attachment; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_attachments
    ADD CONSTRAINT uq_question_attachment UNIQUE (question_id, attachment_name);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_assessments_course; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_assessments_course ON public.assessments USING btree (course_id);


--
-- Name: idx_contexts_assessment; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_contexts_assessment ON public.contexts USING btree (assessment_id);


--
-- Name: idx_questions_assessment; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_assessment ON public.questions USING btree (assessment_id);


--
-- Name: idx_questions_context; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_context ON public.questions USING btree (context_id);


--
-- Name: idx_questions_original; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_original ON public.questions USING btree (original_id);


--
-- Name: idx_questions_previous; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_previous ON public.questions USING btree (previous_version_id);


--
-- Name: assessments assessments_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(course_id) ON DELETE CASCADE;


--
-- Name: assessments assessments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- Name: context_attachments context_attachments_context_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.context_attachments
    ADD CONSTRAINT context_attachments_context_id_fkey FOREIGN KEY (context_id) REFERENCES public.contexts(context_id) ON DELETE CASCADE;


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
-- Name: questions fk_questions_original; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT fk_questions_original FOREIGN KEY (original_id) REFERENCES public.questions(question_id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;


--
-- Name: questions fk_questions_previous; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT fk_questions_previous FOREIGN KEY (previous_version_id) REFERENCES public.questions(question_id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;


--
-- Name: question_attachments question_attachments_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_attachments
    ADD CONSTRAINT question_attachments_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(question_id) ON DELETE CASCADE;


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
    ADD CONSTRAINT questions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- PostgreSQL database dump complete
--

\unrestrict XqIqqmPNdjI1ETTydpsvRJLurltaqeG1QgfVIUaLfK8aaXCJtiJZrYz0cZMsPSc

