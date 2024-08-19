import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {Subject, takeUntil} from "rxjs";
import {AssistantService} from "../../service/assistant.service";
import {CommonModule} from "@angular/common";
import {MatTableModule, MatTableDataSource} from "@angular/material/table";
import {MatFormField, MatFormFieldModule} from "@angular/material/form-field";
import {MatInput, MatInputModule} from "@angular/material/input";
import {MatPaginator} from "@angular/material/paginator";
import {MatSelectChange, MatSelectModule} from '@angular/material/select';
import {MatStep, MatStepper} from "@angular/material/stepper";
import {MatButton} from "@angular/material/button";

@Component({
  selector: 'app-bank-transactions',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatFormField, MatInput, MatFormFieldModule, MatInputModule, MatSelectModule, MatStepper, MatStep, MatButton],
  templateUrl: './bank-transactions.component.html',
  styleUrl: './bank-transactions.component.scss'
})
export class BankTransactionsComponent implements OnInit, OnDestroy{


  unsubscribe: Subject<void> = new Subject();
  dataSource: MatTableDataSource<any, MatPaginator> = new MatTableDataSource<any, MatPaginator>();
  displayedColumns: string[] = [];
  availableTransactionTypes: any[] = [];
  transactionsLoaded: boolean = false
  transactionsClassified: boolean = false
  transactionsSaved: boolean = false

  constructor(private assistantService: AssistantService) {
  }

  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

  ngOnInit() {
    this.assistantService.bankTransactionsSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(transactions => {
        console.log('transactions: ', transactions, 'property name: ', Object.getOwnPropertyNames(transactions['bank_transactions'][0]));
        this.dataSource = new MatTableDataSource(transactions['bank_transactions']);
        if(transactions['available_transaction_types']){
          this.availableTransactionTypes = transactions['available_transaction_types']
        }
        this.displayedColumns = Object.getOwnPropertyNames(transactions['bank_transactions'][0])
        // console.log('transactions: ', transactions, 'dataSource', this.dataSource, 'displayedColumns: ', this.displayedColumns)
      })
    this.assistantService.toolProgressSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe( completedTool => {
        if(completedTool === "load_transactions"){
          this.transactionsLoaded = true
        }
        if(completedTool === "classify_transactions"){
          this.transactionsClassified = true
        }
        if(completedTool === "save_transactions"){
          this.transactionsSaved = true
        }
      })
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }

  async updateTransactionType(changeEvent: MatSelectChange, element: any) {
    console.log(changeEvent)
    console.log(element)
    // await this.assistantService.updateTransactionType()

  }

  confirmTransactions(){

  }
}
