import {LiveAnnouncer} from '@angular/cdk/a11y';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {Component, inject, Input, OnChanges, OnDestroy, OnInit, signal, SimpleChanges} from '@angular/core';
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
import {MatButton, MatIconButton} from "@angular/material/button";
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {MatChipEditedEvent, MatChipInputEvent, MatChipsModule} from '@angular/material/chips';
import {MatIconModule} from "@angular/material/icon";
import {CdkMenu, CdkMenuTrigger, CdkMenuItem, CdkMenuBar} from "@angular/cdk/menu";
import {MatChipGrid, MatChipRow} from "@angular/material/chips";
import {MatCheckbox} from "@angular/material/checkbox";
import {TransactionsService} from "../../service/transactions.service";

export interface Filter {
  column: string
  text: string;
  include: boolean;
  enabled: boolean;
}

@Component({
  selector: 'app-transactions',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatFormField,
    MatInput,
    MatFormFieldModule,
    MatChipsModule,
    MatInputModule,
    MatSelectModule,
    MatStepper,
    MatStep,
    MatButton,
    MatIconModule,
    ReactiveFormsModule,
    CdkMenu,
    CdkMenuBar,
    CdkMenuItem,
    CdkMenuTrigger,
    MatIconButton,
    MatChipGrid,
    MatChipRow,
    MatCheckbox,
    FormsModule,
  ],
  templateUrl: './transactions.component.html',
  styleUrl: './transactions.component.scss',
  animations: [
    trigger('detailExpand', [
      state('collapsed,void', style({height: '0px', minHeight: '0'})),
      state('expanded', style({height: '*'})),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
})
export class TransactionsComponent implements OnInit, OnChanges, OnDestroy{

  @Input() transactions!: Record<string, any>;
  unsubscribe: Subject<void> = new Subject();
  originalDataSource: Record<string, any>[] = [];
  filteredDataSource: MatTableDataSource<any, MatPaginator> = new MatTableDataSource<any, MatPaginator>();
  columnsToDisplay: string[] = [];
  columnsToDisplayWithExpand: string[] = [];
  expandedElement:  any | null
  readonly filters = signal<Filter[]>([]);  readonly announcer = inject(LiveAnnouncer);
  readonly addOnBlur = true;
  readonly separatorKeysCodes = [ENTER, COMMA] as const;

  availableTransactionTypes: any[] = [];
  transactionsLoaded: boolean = false;
  transactionsClassified: boolean = false
  transactionsSaved: boolean = false


  constructor(private assistantService: AssistantService, private transactionService: TransactionsService) {
  }

  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

  async ngOnInit() {
    this.extractTransactionData(this.transactions);

    this.assistantService.toolProgressSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe( completedTool => {
        console.log(`tool completed:${completedTool}`)
        if(completedTool === "load_transactions"){
          this.transactionsLoaded = true;
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

    this.transactionService.filterSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe(( command => {
        this.assistantService.updateTransactions(this.filterMaps(this.originalDataSource, this.filters()), command)
      }))
  }

  async ngOnChanges(changes: SimpleChanges){
    if (changes['transactions']){
      this.extractTransactionData(changes['transactions'].currentValue)
    }
  }

  private extractTransactionData(transactions: any) {
    console.log('transactions: ', transactions, 'property name: ', Object.getOwnPropertyNames(transactions['transactions'][0]));
    this.originalDataSource = transactions['transactions'];
    this.filteredDataSource = new MatTableDataSource(transactions['transactions']);
    if (transactions['available_transaction_types']) {
      this.availableTransactionTypes = transactions['available_transaction_types']
    }
    this.columnsToDisplay = Object.getOwnPropertyNames(transactions['transactions'][0])
    this.columnsToDisplayWithExpand = [...this.columnsToDisplay, 'expand'];
  }

  private filterMaps(maps: Record<string, any>[], filters: Filter[]): Record<string, any>[] {
    if (filters.filter(f=>f.enabled).length === 0) {
      return maps;
    }

    return maps.filter(map => {
      for (const filter of filters) {
        if (!filter.enabled) continue;

        const value = map[filter.column];
        const containsText = value && value.toString().toLowerCase().includes(filter.text.toLowerCase());

        if (filter.include && containsText) {
          return true;
        }

        if (!filter.include && containsText) {
          return false;
        }
      }

      return false;
    });
  }

  add(event: MatChipInputEvent): void {
    const value = (event.value || '').trim();
    let split = value.split(":")

    if (value) {
      this.filters.update(filters => [...filters, {column: split[0], text: split[1], include: true, enabled: true}]);
    }
    event.chipInput!.clear();
  }

  addFilter(column: string, value: string, include: boolean) {
    if (column && value){
      this.filters.update(filters => {
        filters.push({column: column, text: value, include: include, enabled:true})
        let filtered = this.filterMaps(this.originalDataSource, filters)
        this.filteredDataSource = new MatTableDataSource(filtered)
        return filters
      })

    }
  }

  remove(filter: Filter): void {
    this.filters.update(filters => {
      const index = filters.indexOf(filter);
      if (index < 0) {
        return filters;
      }

      filters.splice(index, 1);
      let filtered = this.filterMaps(this.originalDataSource, filters)
      this.filteredDataSource = new MatTableDataSource(filtered)
      this.announcer.announce(`Removed ${filter.text}`);
      return [...filters];
    });
  }

  edit(filter: Filter, event: MatChipEditedEvent) {
    const full = event.value.trim();
    console.log(`editing ${full}`)
    // Remove filter if it no longer has a name
    if (!full) {
      this.remove(filter);
      return;
    }

    const regex = /^([+-])(.*?):\s*(.*)$/;
    const match = full.match(regex);

    if (match) {
      const [, action, column, value] = match;
      this.filters.update(filters => {
        const index = filters.indexOf(filter);
        if (index >= 0) {
          filters[index].include = action == "+";
          filters[index].column = column;
          filters[index].text = value;

          let filtered = this.filterMaps(this.originalDataSource, filters)
          this.filteredDataSource = new MatTableDataSource(filtered)

          return [...filters];
        }

        return filters;
      });
    }
  }

  toggle(filter: Filter, event: Event): void {
    event.stopPropagation()
    filter.enabled = !filter.enabled;
    let filtered = this.filterMaps(this.originalDataSource, this.filters())
    this.filteredDataSource = new MatTableDataSource(filtered)
  }

  async updateTransactionType(changeEvent: MatSelectChange, element: any) {
    console.log(changeEvent)
    console.log(element)

    let toUpdate = this.originalDataSource.find((record) => {
      for (const key in element) {
        if (key != 'transaction_type' && element.hasOwnProperty(key)) {
          if (record[key] !== element[key]) {
            return false;
          }
        }
      }
      return true;
    });
    if (toUpdate){
      console.log(`updating transaction type to:${element['transaction_type']}`)
      toUpdate['transaction_type'] = element['transaction_type']
    }
  }

}
