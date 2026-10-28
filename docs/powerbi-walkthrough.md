# Power BI assignment walkthrough (copied from Canvas, Oct 28 2026)
# Source of the E-Presso file names, table descriptions, relationships, and the textbook reference figures.

Using Power BI - Assignment Walkthrough
Getting Started with Power BI
Microsoft offers four Power BI software products tailored to the needs of specific users and markets. The products in the Power BI suite are designed to work together. A typical user might generate a Power BI report using Power BI Desktop, publish it on the Power BI service, and distribute it using the Power BI Mobile app. We are going to explore a few of the many features of Power BI Desktop, but much of the content and concepts covered here can also be applied to Power BI Pro and Power BI Premium.

Product	Description	Designed For
Power BI Desktop	A free desktop application for the Windows operating system that can connect to hundreds of data sources; provides a wealth of tools to analyze data and prepare summary reports that can be published to Power BI service	Home and small business users who need business intelligence tools for projects of limited scope and size
Power BI Pro	A commercial version of Power BI Desktop; supporting additional tools for managing data quality and information flow and allowing users to create collaborative analyses based on shared data and to distribute that content through customized applications	Power users and companies who require more control over the business intelligence and business analytic processes
Power BI Premium	A commercial version that expands on Power BI Pro by allowing users to distribute reports and other content inside and outside of their organization through the Power BI Server and to create customized BI solutions	Corporate users who need to create their own enterprise solutions for cloud-based analytics
Power BI Mobile	A free mobile app to view and share Power BI reports stored on the Power BI service or from third-party Power BI Servers	Mobile users who need to access Power BI reports and analytics from the Power BI service, but do not need to create their own reports
 

To use Power BI, you must first create an account with the Power BI service. If you have an Office 365 subscription(which you do through MSU), then you already have an account. 

After establishing an account, go to the Power BI webpage (app.powerbi.com), refer to the figure below , and sign in. Because the web is constantly changing, the page you load might not exactly match the page in the figure. The Power BI website includes a navigation pane to access your own content as well as content shared with you from others. You can also retrieve data and Power BI content from third-party vendors, providing you with access to a multitude of public SaaS providers such as Azure Data, Bing, GitHub, and Google Analytics. The Power also BI webpage includes a workspace to review dashboards, reports, workbooks, and datasets available to your Power BI account. Finally, you can integrate your workflow with Microsoft Fabric to create customized solutions for data analytics and management.

image.png

To start Power BI Desktop and create a report
From the Windows 11 desktop, use the Start menu to locate the Power BI Desktop app and open it.

If you are not already signed in, click Sign in located at the top-right edge of the Power BI Desktop title bar. Complete the sign in process by entering your account name or email address and password.
The Power BI Desktop app opens with an untitled screen. Refer to Figure 2.

FIGURE 2

image.png

Click the Blank Report button to open a blank report. Refer to Figure 3.

image.png

The Power BI Desktop window is divided into several sections. The Navigation bar includes buttons to switch between Report view for viewing Power BI reports, Data View for viewing data, and Relationships view for defining the relationship between data tables.

The canvas is a workspace for displaying Power BI reports, datasets, and data models. On the right side of the window, the Filters pane contains tools for filtering the report to highlight subsets of the data, the Visualizations pane contains tools for creating charts and tables, and the Data pane contains information on the data used in the report.

As you develop a Power BI report, you will work through the following stages:

Data connection—Retrieving data from one or more data sources and editing the data as necessary before performing an analysis.

Data analysis—Exploring data with the Power BI visualization tools.

Reporting—Combining the visualizations on one or more pages to summarize your insights.

Publishing—Publishing your content to your Power BI account.

You will follow these stages as you develop an analysis of the five-year sales data for E-Presso.

Connecting to a Data Source
Power BI connects with a wide variety of data sources, from basic text files to large online information systems. Figure 5 describes the general categories of data sources and lists a few of the more popular sources you can access directly from Power BI Desktop.

Figure 5
Power BI data sources
Data Source	Description
File	Data stored in a standalone file, including Excel workbooks, text or CSV files, XML files, JSON files, and SharePoint folders
Database	Data stored in a relational database, including SQL server databases, Microsoft Access, Oracle, IBM DB2, and MySQL
Azure	Data available through the Microsoft business cloud computing service, Azure
Online services	Data available through online services, including SharePoint, Microsoft Exchange, Google Analytics, Facebook, and the Power BI service

To connect to a data source, use the Get Data button in the Data group on the Home tab of the Power BI Desktop ribbon.

An often-used data format is a text file in which data columns are separated using a common symbol such as a comma or a tab. Amber has data about the E-Presso stores stored in a text file with the columns separated by the tab character. You will use the Get Data button now to retrieve that data and bring it into Power BI.

To connect to a text file
On the Home tab, in the Data group, click the Get data button. The Get Data dialog box opens. Refer to Figure 6.

Figure 6:Get Data dialog box
The Get Data dialog box. The left pane includes a list of the categories of data sources such as All, File, Database, Microsoft Fabric, Power Platform, Azure, Online Services, and Other. The All category is selected. The right pane displays all the data sources for the selected category. The Connect button at the bottom of the dialog box connects to a file of the selected data source format.

2.In the All box, click Text/CSV to select the data source type.
3.Click Connect. The Open dialog box opens.
4.Navigate to where you downloaded the  Support_EX_B_Stores.csvDownload Support_EX_B_Stores.csv file, and then click Open. Power BI establishes a connection to the CSV file and opens a preview of the file contents. Refer to Figure 7.
Figure 7:Preview of the Support_EX_B_Stores.csv file
Preview of the Support_EX_B_Stores.csv file, displaying a preview of the data values. There are three dropdown options at the top. The Delimiter option allows you to choose the character that separates the columns. At the bottom, the Load button loads the data into Power BI. The Transform Data button transforms the data before loading.
5.Click Transform Data. The Power Query Editor window opens. Refer to Figure 8
Figure 8: Power Query Editor
The Power Query Editor window. The left pane contains a list of all the available queries. The middle pane contains a preview of the data at the selected step in the query. The right pane contains query settings with Properties and Applied Steps sections. In the Properties section, the query name is entered as, Support_EX_B_Stores. The Applied Steps section lists the steps in query such as Changed Type.
Because the query editor in Power BI has the same interface as the Power Query Editor supplied with Microsoft Excel, you can apply the same techniques to modify the properties of the query that opens this CSV file. The default query name is taken from the file name of the data source. Amber wants you to rename the query as “E-Presso Stores.”

To rename the query as “E-Presso Stores”
1.In the Query Settings pane, click the Name box, and then select and delete the default query name.
2.Type E-Presso Stores in the Name box, and then press ENTER. The query is renamed.
You don’t need every column in the CSV file. Amber wants you to remove the Phone and Manager fields from the query.

To remove the Phone and Manager columns from the query:
1.Click the Phone column header to select the entire column.
2.Hold down CTRL and click the Manager column header to add that column to the selection, and then release CTRL.
3.On the Home tab, in the Manage Columns group, click the Remove Columns button. The Phone and Manager columns are removed from the query.
 

Because you removed the two columns from the query, a new step titled “Remove Columns” is added to the list of applied steps.

When Power Query opens a data source, it automatically assigns data types to the fields contained within the source. Figure 9 lists the data types supported by Power Query.

Figure 9
Power Query data types
Data Type	Used For
Decimal Number	Decimal values such 3.2, 85.7, and 217.06
Fixed decimal number	Decimal values fixed to a specific number of places after the decimal point
Whole Number	Integer values such as 3, 85, and 217
Percentage	Percentages such as 50%, 18.2%, and 99.9%
Date/Time	Values containing both a date and time such as 12/23/2029 11:26:38 AM
Date	Dates such as 12/23/2029
Time	Times such as 11:26:38 AM
Date/Time/Timezone	Values containing dates, times and timezones, such as 12/23/2029 11:26:38 AM +4:00
Duration	Values containing a time duration such as 00:06:45
Text	Text strings such as “coffee” and “Espresso Machine”
True/False	Values limited to True or False
Binary	Values limited to 0 or 1
Defining a data type is not just for appearance. The Power BI analytic tools handle data differently depending on their type. A column containing numeric data is treated as a quantity that can be calculated using measures such as the average and sum, whereas a column containing text is used to break up an analysis into different categories.

The values of the PostalCode field are treated as whole numbers. Although postal codes appear to be numeric, it does not make sense to treat them as numbers (after all, the average value of a set of postal codes has no real meaning). It makes more sense to treat postal codes as text. You can do this by changing the data type for all values in the PostalCode column. You’ll make this change to the query now.

To change the Postal code field data type
1.Click the PostalCode column header to select the column.
2.On the ribbon, click the Transform tab, and then in the Any Column group, click the Data Type button (currently displaying “Whole Number”). A list of data types appears.
3.Click Text in the list. A new step named “Changed Type1” is added to the Applied Steps list. Refer to Figure 10.
Figure 10: PostalCode field data type changed to text
In the Power Query Editor, the Postal Code column is selected as the text data type. The Data Type Text button in the Any Column group changes the data type of the selected column. In the query settings pane, the new query name is entered as E-Presso Stores. The steps are added to the query in Applied steps section, which includes Changed Type 1.
Trouble?
If the Query Editor asks if you want to replace the data type assignment for the field made in a previous step, indicate that this change should be placed in its own step.

You’ve finished editing the query that retrieves the stores data. You’ll apply the query and then load the data into Power BI.

To complete the query
1.On the ribbon, click the Home tab.
2.In the Close group, click the Close & Apply button. The query changes are applied, and the data is loaded in Power BI.
Power BI loads data from the data source using the query as guide. You can display the data by clicking the Table View button on the Navigation bar.

Connecting to Data Stored in Excel
The process for retrieving data is very similar across data sources: You specify the source and then use the Query Editor to make any changes to the data before importing them into Power BI. Amber has data from a customer survey in an Excel workbook that she also wants included in a Power BI report. You will connect to that workbook, selecting the worksheet containing data for Amber’s report and using the Query Editor to transform the data before bringing it into Power BI.

To retrieve the customer survey data from Amber’s Excel workbook
1.On the Home tab, in the Data group, click the Get data button. The Get Data dialog box opens.

2.Verify that Excel Workbook is selected in the list of data source types, and then click Connect. The Open dialog box opens.
3.Navigate to your Data Files, select the Support_EX_B_Survey.xlsxDownload Support_EX_B_Survey.xlsx
 workbook, and then click Open. The Navigator dialog box opens.

4.In the list of worksheets, click the Survey Results check box to select it. A preview of the worksheet appears in the right pane. Refer to Figure 11.
5.Click Transform Data. The Power Query Editor window opens, so you can edit the query used to retrieve the worksheet data.
Figure 11 Navigator dialog box for an Excel workbook

image.png

The first two rows of the selected worksheet do not contain data but instead contain a sheet title and a blank row. You’ll remove those rows and then edit the rest of the query.

To edit the Excel query
1.On the Home tab, in the Reduce Rows group, click the Remove Rows button, and then click Remove Top Rows. The Remove Top Rows dialog box opens.
2.In the Number of rows box, type 1, and then click OK. The top row is removed, and a new step is added to the query.
3.On the Home tab, in the Transform group, click the Use First Row as Headers button. The text from the first row in the query is used as the field names. Refer to Figure 12
Figure 12 Modified Query
image.png
4.In the Close group, click the Close & Apply button. The Survey Results data loads into Power BI Desktop.
Note that the Query Editor automatically added a step to the query to set the data types based on the values found in the worksheet columns. This is another way that the Query Editor helps you load data in the correct format.

Insight Publishing a Workbook to Power BI
Excel and Power BI are tightly integrated. Any Excel workbook can be a data source for a Power BI report, but also any Excel workbook can itself be published to your Power BI account. To publish an Excel workbook, do the following:

In Excel, on the ribbon, click the File tab to open Backstage view, and then click Publish.

To upload the workbook to your Power BI account, click Upload.

To export the data in the workbook to Power BI to be used in other reports, click Export.

If you are prompted, log into your Power BI account.

Depending on your connection to the Power BI service, it might be several minutes before the workbook is listed on your account. Once the workbook has been published, it can be accessed using your web browser or the Power BI mobile app. If you or your colleagues want to continue editing that workbook, you can use the Excel online tools to continue the revision process.

The last piece of data that Amber needs for the analysis is information on sales and products sold by E-Presso. This data is stored in an Access database.

Connecting to Data Stored in Access

Access is the database application in the Microsoft Office suite, so it is well-integrated with Power BI Desktop. You can load any table or query created in Access into Power BI as another data source. Amber has an Access database with two tables containing information on the products and product categories of items sold by E-Presso and a third table containing monthly sales totals from the past five years for each product and product category. You will add those three tables to Power BI Desktop now.

To connect to the sales totals in Amber’s Access database
1.On the Home tab, in the Data group, click the Get Data button. The Get Data dialog box opens.
2.In the All box, click Database as the data source, click Access database from the list of database types, and then click Connect.
3.Navigate to your Data Files, click Support_EX_B_Sales.accdbDownload upport_EX_B_Sales.accdb in the file list, and then click Open. The Navigator dialog box opens, listing the tables and queries in the database.
Trouble?
If Power BI displays an error message indicating that it is unable to connect, follow the instructions in the dialog box to install the Access Database Engine from the indicated website, and then click Retry once it’s installed. Make sure you use the Access Database Engine that matches your operating system.

4.Click the Categories, Products, and Sales check boxes to select those tables from the database. You do not have to edit the query for these tables. Refer to Figure 13.
Figure 13 Navigator dialog box for an Access database
image.png
5. Click Load to load the tables into Power BI without going through the Query Editor.
6. In the Navigation bar, click the Table view button  to display the contents of tables imported into Power BI. The Categories table is currently open in Data view. Refer to Figure 14
Figure 14 Table view in Power BI desktop
image.png
You have all the data required for Amber’s analysis.  Figure 15 summarizes the data stored in each of the five tables. If you want to change the queries that created any of the five tables, select the table in Data view, and then click the Transform Data button in the Queries group on the Home tab.

Figure 15 Data tables
Table	Description	Fields
Categories	Describes the general categories of items sold by E-Presso	Category, Category ID
E-Presso Stores	Provides data on the 20 stores and the company website	City, ID, Location, Market, State, StoreType, PostalCode
Products	Describes the products sold by E-Presso	Product, Product ID
Sales	Provides monthly sales revenue for each of 20 stores and the company website, broken down by category and product ID, over a five-year period from 2025 to 2029	Category ID, Date, Product ID, Revenue, Sales ID, Store ID, StoreYear
Survey Results	Provides the results of yearly market surveys taken at the 20 stores gauging customer satisfaction and general interest in company products from 2025 to 2029	Interest, Satisfaction, Store ID, Survey ID, Year
There is no connection between the tables in the database and the tables created from the CSV file and the Excel workbook. You will connect those tables next.

Defining Table Relationships in Power BI
Power BI Desktop provides the same tools found in Power Pivot to create relationships between multiple tables within a data model. As with Power Pivot, relationships are defined by matching fields that are common to pairs of tables. To view the relationships in the data model, you will go to the Model view of the data.


To switch to Model view
1. On the Navigation bar, click the Model view button  to switch to Model view.
2. Click and drag the tables by their title bars into the layout in Figure 16
Figure 16 Model view in Power BI Desktop
image.png

Tip
You can change the magnification of Model view by clicking the zoom slider in the lower-right corner of the Power BI Desktop window.

A line connects the tables for which a relationship exists between the fields in the tables. The Categories and Sales table are connected via the common Category ID field. The Products and Sales table are connected via the common Product ID field. There is no relationship for the E-Presso Stores and Survey Results tables. Because those tables are currently unrelated to information found in any other table, you must define the relationships yourself. You create these relationships with the Manage Relationships tool. You will create a relationship connecting the Survey Results table to the Sales table through the Survey ID and StoreYear fields.

To create table relationships between the Survey Results and Sales tables
1.On the Home tab, in the Relationships group, click the Manage relationships button. The Manage relationships dialog box opens, listing the relationships currently defined in the data model.
2.Click New relationship to create a new relationship.

Tip
You can also create a relationship in Model view by dragging a field name from one table onto its common field in another table.

3.Click the From table box, click Survey Results in the list of tables, and then click the Survey ID column header to select it.
4.Click the To table box, click Sales in the list of tables, and then click the StoreYear column header to select it. Refer to Figure 17
Figure 17 New relationship dialog box
image.png
5.Click Save to create the relationship.
Next, you will create a relationship that connects the E-Presso Stores table to the Survey Results table through the ID and Store ID fields.

To relate the E-Presso Stores and Survey Results tables
1.In the Manage relationships dialog box, click New relationship.
2.Click the From table box, click E-Presso Stores in the list of tables, and then click the ID column header.
3.Click the To table box, click Survey Results in the list of tables, and then click the Store ID column header. A one-to-many relationship is created between the two tables.
4.Click Save to create the relationship.
5.Click Close to close the Manage relationships dialog box and return to Model view.
Connecting lines are now added to the Model view diagram connecting the E-Presso Stores table to the Survey Results table and the Survey Results table to the Sales table. Before examining the data, you should save the current report and the information about the data sources and the relationships between the tables.


To save the Power BI report
1.On the Power BI Desktop window, click the File menu and then click Save as.
2.At the bottom of the window, click Browse this device.
3.Navigate to the ExcelB > Module folder included with your Data Files.
4.In the File name box, enter NP_EX_B_EPresso and verify that the .pbix file extension is selected.
5.Click Save.
Power BI Report files are saved with the .pbix file extension by default, storing the data and the reports generated for that data.

You can save the document as a Power BI template file in which the structure and forms of the document are preserved for use with other data sources and other analyses. Templates are useful when you want to apply the same formatting across multiple Power BI reports. Templates are saved with .pbit file extension.

You can also save your report as a Power BI project file with the .pbip file extension. A project file includes version control features with contents stored in a Power BI report folder structure. The report folder contains the report, pages, model diagrams, and visualizations.

Analyzing Data with Power BI
The great power of Power BI is that it quickly and seamlessly presents data in various ways, uncovering hidden relationships and trends. Amber has some questions she wants investigated, including:

What is the pattern for monthly sales? Which months have the highest sales volume? Which months are the lowest? What has been the sales trend over the past five years?

What is the revenue from the 20 stores and the company website? Is the website becoming more profitable than the stores?

What factors affect revenue? Is greater revenue associated with higher customer satisfaction? Is customer satisfaction the same at all stores?

To begin answering these questions, you will go to the Report section of Power BI Desktop and analyze the data using visualizations.

 

 

Creating a Visualization
A visualization or visual is any Power BI chart, table, or graphic that conveys information about the data. The selection of visualizations appears in the Power BI Desktop Report view, organized with the Visualizations pane. Figure 18Links to an external site. describes some of the many visualizations available with Power BI.

Figure 18 Power BI visualizations
Visualization	Description
image.png	A stacked bar chart summarizes data in separate bars with each bar divided into categories.
image.png	A stacked column chart summarizes data in separate columns with each column divided into categories.
image.png	A clustered column chart summarizes data in separate column groups and each group divided into separate categories.
	A line chart displays data as separate lines across categories.
image.png	A line and stacked column chart combines visualizations from both a stacked column chart and a line chart.
image.png	A scatter chart displays the correlation between two numeric variables.
image.png	A map displays data based on their locations on a world globe.
image.png	A filled map displays data based on their locations in geographic regions on a world map.

More visualizations are being added all the time as Power BI provides new ways of interpreting data. To add a visualization to a report page, click a visualization button in the Visualizations pane to insert a blank visualization of that type into the current page. Amber wants you to add a stacked bar chart visualization to the report that will compare the total revenue from the company’s website to the revenue generated by its brick-and-mortar stores.

To add a stacked bar chart visualization
1.On the Navigation bar, click the Report view button 
2.If the Filters pane is expanded, click the Collapse arrow in the upper-right corner of the pane to hide it, leaving only the Visualizations and Data panes expanded.
3.In the Visualizations pane, click the Stacked bar chart button image.png (the first visualization listed in the pane). An empty bar chart is added to the upper-left corner of the report page. Refer to Figure 19
Figure 19 Blank stacked bar chart visualization
image.png

Once you have added a blank visualization to a page, you can build the visualization by dragging fields from the data tables into the different visualization areas. In a bar chart, the length of each bar is proportional to the size of its underlying numeric field. Since Amber wants to know if E-Presso collected more revenue from all 20 brick-and-mortar stores or from its website, you will add the Revenue field from the Sales table and the StoreType field from the E-Presso Stores table to the bar chart.

To review sales by store type
1.In the Data pane, click the Expand arrow next to Sales to display the field list for that table.
2.Drag the Revenue field from the field list and drop it below the X-axis label into the “Add data fields here” box in the Visualizations pane. The bar chart shows the total revenue from across all stores.
3.Click the Expand arrow next to the E-Presso Stores table name to display its field list.
4.Drag StoreType from the E-Presso Stores field list and drop it below the Y-axis label into the “Add data fields here” box. The revenue totals are broken down by store type—Brick & Mortar and Website.
5.Drag the lower-right sizing handle on the bar chart down and to the right so that the bar chart fills the left third of the report page. Refer to Figure 20.
Figure 20 Bar chart of revenue by store type
image.png

Website revenue from the select group of products over the past five years is between $20 million and $30 million, while revenue for those same products from the brick-and-mortar stores is about half of that amount.


Tip
You can display the exact revenue numbers by hovering your pointer over each bar.

The labels and axes text are difficult to read because of their small font size. You can correct this issue by formatting the bar chart.

Formatting a Visualization
You can format elements within a visualization by selecting the Format visual button image.png in the Visualizations pane to display a list of elements within the visualizations. The gallery of formatting choices is very large. You can change font size, text and fill color, font styles, and turn elements on and off. In this chart, you will use the formatting tools to increase the font size of the y-axis labels, remove the x-axis, and add data labels to each bar.

To format the bar chart
1.At the top of the Visualizations pane, click the Format visual button image.png to open a list of formatting categories.
2.With the Visual tab selected, click Y-axis to open the formatting options for the chart’s y-axis.
3.Next to Title, click the on/off button to turn off the y-axis title, hiding the label StoreType in the chart.
4.Click the Values label below the Y-axis title to open a gallery of formatting options for the bar chart values, if necessary.
5.Use the Font size box to set the font size value to 12.
6.Click X-axis to display formatting options for the chart’s x-axis.
7.Click the on/off button next to Title to turn off the X-axis title, hiding the label, Sum of Revenue.
8.Click the on/off button next to Values to hide the axis of revenue values below the bar chart.
9.Scroll down the Visualizations pane and click the on/off button next to Data Labels to include data labels in the bar chart.
10.Click the Data Labels title to open a gallery of formatting options for the data labels.
11.In the Options section, click the Position box, and then select Inside end so that data labels are included inside and at the end of each bar.
12.In the Data labels section, click the Value title to open options for formatting the data label text.
13.Increase the font size of the data labels to 15. Refer to Figure 21
Figure 21 Formatted stacked bar chart
image.png
The analysis shows that E-Presso has accumulated about $42 million in revenue over the past five years from a select group of products, with about $27 million collected the website and $15 million from the brick-and-mortar stores.

Amber wants you to change the title of the chart to “Total Revenue by Store Type.” You will make that change now.


To change the chart title
1.In the Visualizations pane, in the Format visual section, click the General tab to access general formatting choices for the chart and elements within the chart.
2.Click Title in the list of general items.
3.In the Text box, change the chart title from “Sum of Revenue by StoreType” to Total Revenue by Store Type.
4.Increase the font size to 20.
5.In the horizontal alignment section, click the Center button  to center the chart title text. Refer to Figure 22.
image.png

 

Creating a Line Chart
Line charts are used to compare data values across evenly spaced categories arranged in a sequential order, such as the months within a year or years across a date interval. Amber wants to review the revenue figures for each of the past five years. You will add that information with a line chart to the Power BI report that tracks annual revenue over the past five years.

To create a line chart of revenue by year
1.Click a blank space on the report page to deselect the bar chart.
Tip
Clicking a visualization type when a visual is selected changes that visual’s type instead of creating a new visual.

2.In the Visualizations pane, click the Line chart button image.png . A blank line chart is added to the report page.
3.In the Data pane, drag the Revenue field from the Sales table and drop it in the Y-axis box in the Visualizations pane.
4.In the Sales table, click the Date arrow to display the Date Hierarchy label.
5.Click the Date Hierarchy arrow to display fields for Year, Quarter, Month, and Day.
6.Click the Year check box to add the year values to the x-axis of the line chart.
7.Resize the line chart so that it covers the upper-right corner of the report page.
8.Click the Format visual button image.png to display the formatting categories for the line chart.
9.Click the X-axis category, and then click the Values category arrow. Increase the Font size value to 15.
10.Scroll down and click the Y-axis category, click the Values category arrow. and then increase the Font size value to 15.
11.Scroll down to the Data Labels section, and then click the on/off button next to Data Label to display revenue totals on the chart.
12.Click the Data labels arrow, click Value category arrow, and then increase the text size value to 15.
13.Click the General tab, and then click Title.
14.In the Text box, change the title text from “Sum of Revenue by Year” to Total Revenue by Year. Center the title horizontally within the chart and increase the text size to 20 points. Refer to Figure 23
Figure 23 Line chart of annual revenue
image.png
When Power BI encounters a date field, it will automatically create a hierarchy of fields containing the year, quarter, month, and day of the month. You can apply any field within that hierarchy to a visual. If you want to use the actual date instead of the hierarchy, click the field arrow for the date field in your visual and from the shortcut menu, click the name of the field instead of the hierarchy.


From 2025 to 2029, E-Presso’s annual revenue on the select group of products in Amber’s database increased from $7.2 million to $9.2 million—almost a 28% increase in revenue. Amber wants to know whether this increase was constant across all stores and types of stores.

To answer that question, you could drop the StoreType field from the E-Presso Stores table in the Legend box to break the line chart into two lines: one for the brick-and-mortar stores and one for the company’s website. But there’s another way that uses the interactive nature of Power BI visualizations.

Linking Power BI Visuals
The visuals you create in Power BI do not stand alone—they interact with one another. This powerful feature allows you to select categories in one visual and have your selection reflected in the other visual. In this way, you can quickly filter your report across multiple charts and graphics to find trends and relationships within subsets of the entire data.

You will use this feature of visual filtering to review the yearly revenue for brick-and-mortar stores and then for the company website.

To review yearly revenue within types of stores
1.On the bar chart, click the Brick & Mortar bar. The line chart is filtered to show only the yearly revenue from the brick-and-mortar 20 stores. Refer to Figure 24
Figure 24 Annual revenue for the brick-and-mortar stores
image.png
2.Click the Website bar in the bar chart to include yearly revenue from only the website. Refer to Figure 25
Figure 25 Annual revenue for the website
image.png
3.Click the Website bar again to remove the filtering from the report page, including revenue from both the brick-and-mortar stores and the website.
There is huge difference between the revenue history for the 20 brick-and-mortar stores compared to the website. Revenue for select products from the brick-and-mortar stores decreased from $4.0 million to $2.2 million, a 45% decline over five years, while revenue from the website increased from $3.2 million to $7.0 million, an increase of about 118%. Although the company overall has shown a steady increase in revenue, this is not true of their brick-and-mortar stores.

Creating a Column Chart
Stacked column charts show values broken down by categories in which the height of each column is proportional to the data value within each category. Amber wants to know whether revenue also varies by month. To explore that question, you will add a column chart of revenue by month to the lower-right quarter of the page.

To create column a column chart of revenue by month
1.Click an empty spot on the page to deselect all the visuals.
2.In the Visualizations pane, click the Stacked column chart button image.png . A blank chart is placed in the lower-right third of the page.
3.Click Month in the Date hierarchy in the Sales table to add that field to the chart’s x-axis.
4.Click Revenue in the Sales table to add that field to the Y-axis area of the column chart.
5.In the Visualizations pane, click the Format visual button image.png to display the formatting categories for the column chart.
6.Set the text size value for both the X axis values and the Y axis values to 12.
7.Add data labels to the chart and set the text size of their values to 12.
8.Click the General tab and then change the chart title to Total Revenue by Month. Set the font size of the title to 20 and center the title horizontally. Refer to Figure 26Links to an external site..
Figure 26 Column chart of revenue by month
image.png
9.Click the Brick & Mortar bar in the bar chart to filter the report, showing only data from the 20 brick-and-mortar stores. Refer to Figure 27.
Figure 27 Monthly revenue for brick-and-mortar stores
image.png.
10.Click the Brick & Mortar bar again to remove the filter.

Over the five years of collected sales data for the selected products, the months with the highest revenue were November and December, with aggregated total revenue of $16.2 million across all 20 stores and the website. There is no indication that the pattern of monthly sales changes between the stores and the website. In each month, the revenue from brick-and-mortar stores appears to be about one-third of the total revenue.

Tip
Chart interaction works both ways: Selecting a data marker from any chart will filter the other charts on the page.

Changing a Measure
Power BI supports measures other than sums, including average, count, minimum, and maximum. Amber thinks it would be more useful to know the revenue by month values as a percentage of the yearly total so that the company can more easily anticipate future monthly trends in sales and revenue.

To apply the percentage measure to the column chart
1.If necessary, click the Total Revenue by Month column chart to select it.
2.At the top of the Visualizations pane, click the Build visual button image.pngto again display the fields associated with the column chart.
3.Click the Sum of Revenue arrow below the Y-axis label to display a list of summary statistics.
Tip
Fields that can be summarized using a measure are identified in the field list with the 'Summation"  icon.

4.From the list of summary statistics, point to Show value as and then click Percent of grand total on the menu. The data labels for each month show the percentage of annual revenue accumulated during the month.
5.Click the Format visual button image.png at the top of the Visualization pane, and then click General.
6.Click Title and then in the Text box, change the chart title to Percent of Annual Revenue per Month. Refer to Figure 28
Figure 28 Column chart of monthly revenue percentages
image.png
7.Click the Brick & Mortar bar from the bar chart. The percentages in the column chart do not change very much, indicating that percentage of sales by month is consistent across store types.
8.Click the Brick & Mortar bar again to remove the filter from the report.
This analysis shows that more than 38% of the company’s annual revenue is collected in November (12.71%) and December (25.61%).

Adding a Slicer
Another way to filter the visuals within a report page is with a slicer. Like slicers used with Excel tables, Power BI slicers filter multiple visuals within a report. Unlike Excel slicers, selections made to a slicer affect only the current Power BI report. If you close the report and reopen it, the previous slicer selections are lost.

Having reviewed the revenue totals across all product categories, Amber wants to explore the revenue trends for specific product categories. To do that analysis, you will add a slicer for the Category field from the Categories table.

To add the Category field slicer to the report page
1.Click the Total Revenue by Store Type bar chart to select it, and then drag the upper-middle resizing handle down to resize the chart to cover the lower-left third of the report page.
2.Click an empty spot in the upper-left quarter of the page to deselect the bar chart.
3.In the Visualizations pane, click the Slicer button image.png in the fifth row and third column of the gallery of visuals. A slicer is added to the upper-left corner of the report page.
4.In the Data pane, click the Expand arrow next to the Categories table. A list of the fields in the table appears.
5.Click the Category check box. Category is added to the Field box and the five product categories appear in the slicer.
6.In the Visualizations pane, click the Format visual button image.png to display the formatting categories for the slicer.
7.Click Values in the list of slicer elements, and then set the font size to 18.
8.Click the Slicer header label to display formatting options for the header, and then set the font size to 25. Refer to Figure 29
Figure 29 Product categories displayed in a slicer
image.png
9.In the slicer, click each category check box and note that revenue from coffee beans has declined in the past two years. Refer to Figure 30
Figure 30 Revenue report for bean sales
image.png
10.Click the Beans check box again to remove the slicer filter. All the data is redisplayed.
From this analysis, Amber learned that revenue for Beans and Syrups declined slightly over the past two years while revenue for accessories and espresso machines generally increased. Frothers decreased in 2028 but rebounded in the last year. One possible insight is that E-Presso is showing solid growth in its machines but perhaps is losing revenue in food products such as beans and syrups. That insight might cause the company to rethink how it is marketing its products or perhaps devote more resources to products that will produce the most revenue.

Insight Filtering in Power BI
The interaction between charts is an example of a visual-level filter, in which filtering one visual impacts the other visuals on the page. Other types of filters include a page-level filter that filters everything within a single page and a report-level filter that filters the content of every page in a report spanning multiple pages.

To filter a page, drag a field onto the Filters on this page box located in the Filters pane to the left of the Visualizations pane and select the values in that field that satisfy your chosen filter. To filter the entire report, drag the field into the Filters on all pages box and do the same. Reports can combine several visual-level, page-level, and report-level filters.

Drilling into Data
Another interactive feature that can be applied to Power BI visuals is the ability to drill into the data by moving through a hierarchy of fields from the more general to the more specific. For example, you could drill into the Total Revenue chart by going from all stores down to stores in specific geographic areas, to stores in specific states, and finally down to the sales data for a specific store.

To create a hierarchy of data fields, you add multiple fields to an element of a chart or graphic. Amber wants to explore revenue from stores based on the size of their market and their city location. You will add the Market and City fields to the bar chart.


To add the Market and City fields to the bar chart
1.Click a blank spot in the Total Revenue by Store Type bar chart to make the bar chart the active visualization in the report.
2.If necessary, in the Visualization pane, click the Build visual button image.png to select it.
3.In the Data pane, drag the Market and City fields from the E-Presso Stores table into the Y-axis box, directly below the StoreType field. Note that new buttons appear above the bar chart. Refer to Figure 31
Figure 31 Multiple fields added to the bar chart axis
image.png
Before you can drill into data you must change Power BI to drill mode so that clicking elements of the chart drills into the chart data hierarchy rather than applying a visual filter. You turn on drill mode by clicking the Drill Down buttonimage.png located above the chart. The icon changes to the Drill Mode button image.png , indicating that drill mode is on. At any point while drilling down or up the data hierarchy, you can click the Drill Mode button image.png to turn off drill mode and enable visual filtering.

You’ll use the Drill mode feature to examine the revenue history for major markets and for the Chicago store.

To drill into the Total Revenue by Store Type bar chart
1.At the top of the Total Revenue by Store Type bar chart, click the Drill Down button image.png to turn on drill mode.
2.Click the Next level button image.png to go to the next lower level in the data hierarchy. The chart displays revenue totals for the stores in a Global market (the website), Large, Medium, Minor, and Small markets.
3.Click 4-Large in the list of markets to drill into stores situated in a large market. The three stores of this type are: Phoenix, Baltimore, and Chicago.
4.Click the Drill Mode button image.png to turn off the Drill Down mode.
5.Click Chicago to display the revenue data only for the Chicago store. Refer to Figure 32
Figure 32 Revenue for the Chicago store
image.png
6.Click Phoenix to filter the report to show revenue values for the Phoenix store. Refer to Figure 33
Figure 33 Revenue for the Phoenix store
image.png
7.Click Phoenix again to remove filtering from the report.
8.Click Drill Up button image.png twice to return redisplay the revenue data for both stores and the company website.
Amber is interested in the difference in revenue history between the two stores. The Chicago store suffered a huge decline in annual revenue for the select group of products from $0.54 million in 2025 to $0.18 million in 2029, a 67% decrease. The Phoenix store showed a more limited sales decline from about $0.53 million in 2025 to $0.47 million in 2029, a decrease of about 11%. The company will want to investigate how the Phoenix store was able to control its losses better than the Chicago store as it examines the financial viability of its brick-and-mortar stores.

Working with Report Pages
A report can support multiple pages with each page focusing on a different aspect of the data. In a report with multiple pages, you can distinguish one page from another by giving pages descriptive names. You’ll change the name of the current report page from its default name of “Page 1” to “Revenue Analysis.”

To rename the current report page
1.Double-click Page 1 in the page tab. You can now edit the page tab text.
2.Type Revenue Analysis to replace Page 1 with the new page name, and then press ENTER.
Next, you will add a new page to the report in which you will compare the revenue totals to results from the customer survey to determine whether customer satisfaction is related to total revenue.

To add a new page to the report
1.To the right of the Revenue Analysis page tab, click the New page button image.png . A new page is added to the report with the default name “Page 1.”
2.Double-click Page 1 to begin editing the page name. Replace Page 1 with Survey Analysis and press E N TER.
Amber wants you to look at whether the decline in revenue is related to customer satisfaction measured on a 0 (poor) to 5 (excellent) scale. You can explore that question with a scatter chart that plots the values from two numeric fields to determine whether stores with the highest revenue also have the highest customer satisfaction. You will create a scatter chart plotting sales revenue against customer satisfaction for each store and year.

To create a scatter chart of revenue and customer satisfaction
1.With the Survey Analysis page active, in the Visualizations pane, click the Scatter chart button image.png . A blank scatter chart is added to the page.
2.Use the sizing handles to resize the blank scatter chart so that it fills the left half of the page.
3.In the Data pane, click the Expand arrow next to the Survey Results table to display its field list.
4.Drag and drop the Survey ID field from the Survey Results table into the Values box so that a point is plotted for each survey response from the Survey Response table.
5.Drag and drop the Satisfaction field from the Survey Results table into the X-axis box so that the sum of the satisfaction scores is plotted along the horizontal axis.
6.Click the Sum of Satisfaction arrow under the X Axis label and select Average to show the average satisfaction score.
7.Drag and drop the Revenue field from the Sales table into the Y Axis box so that revenue totals are plotted against the vertical axis.
8.Click the Format visual button image.png .
9.Click the X-axis arrow and then click the Title arrow to view formatting options for the X-axis title. In the Title text box, replace Auto with the text Customer Satisfaction.
10.Click the Y-axis arrow and then click the Title arrow to access formatting options for the Y-axis title. In the Title text box, replace Auto with the text Total Revenue.
11.Click the General tab and then click the Title arrow. In the Text box, replace Average of Satisfaction and Sum of Revenue by Survey ID with Total Revenue vs. Customer Satisfaction. Increase the font size of the title text to 20 and horizontally center the text.
12.Click the Build visual button image.png . Refer to Figure 34
Figure 34 Revenue versus Satisfaction scatter plot
image.png
There appears to be a possible increase in revenue with increasing customer satisfaction, but there is a lot of variability in the data. Most of the low satisfaction numbers are clustered below $0.2 million in revenue, while the highest satisfaction numbers range up to $0.5 million. You can often clarify a scatter chart by adding a trend line to the chart highlighting the general trend of the data. Add a trend line to the chart now.


To add a trend line to a scatter chart
1.With the scatter chart still selected, click the Analytics button image.png at the top of the Visualizations pane.
2.Click the Trend line on/off button to turn on the trend line. Refer to Figure 35
Figure 35 Trend line added to a scatter chart
image.png
You can add other lines to a scatter chart such as a line of constant value in the horizontal and vertical direction or a line marking the maximum, minimum, average, or median. You also use a line that marks an overall percentile, such as line that marks the upper 90th percentile of the data. Usually, you only want one analysis line per chart to avoid overwhelming the user.

There is so much that affects revenue, it is unclear how much customer satisfaction contributes to changes in revenue. Clearly this needs to be investigated further to control other factors. One possible factor is the stores themselves. Are some stores doing a better job serving their customers than others? To explore this question, Amber wants you to display a table of the stores listing their average customer satisfaction scores and their total revenue over the past five years.

To create a table of store data
1.Click a blank spot on the right side of the Survey Analysis page to deselect the scatter chart visual.
2.In the Visualizations pane, click the Table button image.png . A blank table visual is added to the right side of the page.
3.Drag City from the E-Presso Stores table into the Columns box. A list of cities is displayed in the first column of the table.
4.Drag the State, Location, Market, and StoreType fields from the E-Presso Stores table into the Columns box so that they appear to the right of the City column.
5.Drag the Revenue field from the Sales table to the Columns box so that the Sum of Revenue column appears to the right of StoreType column.
6.Drag the Satisfaction field from the Survey Results table to the Columns box so that the Sum of Satisfaction appears as the last column in the table.
7.Click the Sum of Satisfaction arrow in the Columns box, and then click Average so that the Average of Satisfaction appears in the table. Refer to Figure 36
Figure 36 Table of store, revenue, and survey data
image.png
As with the Power BI charts, a Power BI table is linked to the other visuals on the page. You will select the Chicago store from the table to display only the Chicago values in the scatter plot.

To select a record from a table visual
1.Click Chicago from the list of records in the table. The scatter plot is revised to show only the five data values from the Chicago store. Refer to Figure 37
Figure 37 Revenue versus Customer Satisfaction for the Chicago store
image.png
2.Click Chicago in the list of table records again to remove the filter from the page.

Tip
Filters applied to a visual in one page will not affect visuals in other pages. To apply a filter across all pages, create a filter in the Filters pane.

Based on this analysis, there is no indication that lower satisfaction scores are associated with lower revenue at the Chicago store. On the other hand, people who no longer frequent the store are not likely to fill out a customer survey. Active customers are a select group that are more likely to be pleased with the store’s service. More research is needed to explain why there was a severe decline in revenue at brick-and-mortar stores in general and at the Chicago store in particular.

Publishing a Power BI Report
After you create a report, you can publish it to your Power BI service account so that it is visible in your web browser and shareable with other members of your team. To publish a report to your Power BI and Microsoft Fabric account, save the report and then select the Publish button in the Share group on the Home tab. Power BI Desktop uploads the data and the visualizations you created to the service, notifying you when the report uploading is complete.

Amber wants you to publish the E-Presso Stores report to your workspace now.

To save and publish the E-Presso Power BI report
1.On the Power BI ribbon, click the File tab, and then click Save. The report is saved with all the changes you made.
2.On the Home tab, in the Share group, click the Publish button. The Publish to Power BI dialog box opens.
3.Click My workspace in the Select a destination box, and then click Select. Power BI begins publishing the report to your Power BI account. The Publishing to Power BI dialog box opens when the report has been published with a link to the report.
4.Click the Open ‘NP_EX_B_EPresso.pbix’ in Power BI link. Your web browser opens to your Power BI account with the report displayed in your workspace. Refer to Figure 38
Figure 38 Power BI report displayed in a web browser
image.png
5.Click the Revenue Analysis tab, review the page, and then close the Power BI report page on your web browser. Do not save any changes you may have made to the report.
6. Return to Power BI Desktop, click Got It in the Publishing to Power BI dialog box, and then close the Power BI Desktop window.
sidenote
Upload and submit your completed project to canvas.  Make sure to be in a "group" with your PowerBI Buddy

From the webpage on the Power BI service, you have access to many of the same tools you used in Power BI Desktop. If you select the Edit report link directly above the report page, the same Visualizations, Filters, and Fields panes available in Power BI Desktop open. To share an interactive version of the report, you and your colleagues must be on the same email domain and have a Power BI Pro or Power BI Premium license.

Insight Publishing for Mobile Devices
Power BI supports a mobile app, so your reports and analyses can be viewed by colleagues on their mobile devices. To create a mobile version of your report, go to the View tab on the Power BI Desktop ribbon, and then in the View group, click the Phone Layout button. Power BI displays a mobile layout that you can use to arrange the visualizations from your report, optimizing them for a mobile phone or PDA. When you publish a report to your Power BI account and share it with your colleagues, anyone viewing your report on the Power BI Mobile app will have a report tailored to the size and specifications of mobile devices.

Amber appreciates the work you’ve done setting up the revenue analysis. She wants you to generate other reports, so you will continue to use Power BI to explore fundamental issues in an ongoing process to improve sales and service at E-Presso.