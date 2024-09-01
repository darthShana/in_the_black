import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {Subject, takeUntil} from "rxjs";
import {AssistantService} from "../../service/assistant.service";
import {TransactionsService} from "../../service/transactions.service";
import {CommonModule, JsonPipe} from "@angular/common";
import untruncateJson from "untruncate-json";
import {MatTableModule} from '@angular/material/table';

interface ReportLine {
  description: string;
  amount?: string;
  subtitle: boolean;
}
@Component({
  selector: 'app-end-of-year-reports',
  standalone: true,
  imports: [
    JsonPipe,
    MatTableModule, CommonModule
  ],
  templateUrl: './end-of-year-reports.component.html',
  styleUrl: './end-of-year-reports.component.scss'
})
export class EndOfYearReportsComponent implements OnInit{

  @Input() eoyReports!: Record<string, any>;
  protected reportLines: ReportLine[] = []
  displayedColumns: string[] = ['description', 'amount'];

  ngOnInit(): void {

    console.log("calculating statement_of_profit_or_loss")
    let profitOrLoss = this.eoyReports['statement_of_profit_or_loss']

    this.reportLines.push({description: "Revenue", amount:undefined, subtitle:true})

    for (let revenueItem of profitOrLoss['revenue_items']){
      this.reportLines.push({description: revenueItem['display_name'], amount:revenueItem['balance'], subtitle:false})
    }
    this.reportLines.push({description: "Total Trading Income", amount:profitOrLoss['gross_profit'], subtitle:true})

    for (let expenseItem of profitOrLoss['expenses_items']){
      this.reportLines.push({description: expenseItem['display_name'], amount:expenseItem['balance'], subtitle:false})
    }
    this.reportLines.push({description: "Total Expenses", amount:profitOrLoss['expenses_total'], subtitle:true})

  }





}
