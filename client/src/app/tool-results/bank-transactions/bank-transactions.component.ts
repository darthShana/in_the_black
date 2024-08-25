import {Component, inject, Input, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {animate, state, style, transition, trigger} from '@angular/animations';
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
import {FormBuilder, ReactiveFormsModule, Validators} from "@angular/forms";
import {MatIcon} from "@angular/material/icon";

@Component({
  selector: 'app-bank-transactions',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatFormField, MatInput, MatFormFieldModule, MatInputModule, MatSelectModule, MatStepper, MatStep, MatButton, ReactiveFormsModule, MatIcon],
  templateUrl: './bank-transactions.component.html',
  styleUrl: './bank-transactions.component.scss',
  animations: [
    trigger('detailExpand', [
      state('collapsed,void', style({height: '0px', minHeight: '0'})),
      state('expanded', style({height: '*'})),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
})
export class BankTransactionsComponent implements OnInit, OnDestroy{

  unsubscribe: Subject<void> = new Subject();
  dataSource: MatTableDataSource<any, MatPaginator> = new MatTableDataSource<any, MatPaginator>();
  columnsToDisplay: string[] = [];
  columnsToDisplayWithExpand: string[] = [];
  expandedElement:  any | null

  availableTransactionTypes: any[] = [];
  transactionsLoaded: boolean = false;
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
        this.columnsToDisplay = Object.getOwnPropertyNames(transactions['bank_transactions'][0])
        this.columnsToDisplayWithExpand = [...this.columnsToDisplay, 'expand'];
        // console.log('transactions: ', transactions, 'dataSource', this.dataSource, 'displayedColumns: ', this.displayedColumns)
      })
    this.assistantService.toolProgressSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe( completedTool => {
        console.log(`tool completed:${completedTool}`)
        if(completedTool === "load_transactions"){
          this.transactionsLoaded = true;
          console.log('transactionsLoaded: ', this.transactionsLoaded )
        }
        if(completedTool === "classify_transactions"){
          this.transactionsClassified = true;
          console.log('transactionsClassified: ', this.transactionsClassified )

        }
        if(completedTool === "save_transactions"){
          this.transactionsSaved = true;
          console.log('transactionsSaved: ', this.transactionsSaved )
        }
      })

  }


  async updateTransactionType(changeEvent: MatSelectChange, element: any) {
    console.log(changeEvent)
    console.log(element)
    // await this.assistantService.updateTransactionType()

  }

}
