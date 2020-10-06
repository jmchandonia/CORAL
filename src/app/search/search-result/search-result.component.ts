import { Component, OnInit, ChangeDetectorRef, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder } from '../../shared/models/QueryBuilder';
import * as $ from 'jquery';
import 'datatables.net';
import 'datatables.net-bs4';
import { Router, ActivatedRoute } from '@angular/router';
import { NgxSpinnerService } from 'ngx-spinner';
import { DatatableComponent } from '@swimlane/ngx-datatable';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { ColumnMode } from '@swimlane/ngx-datatable';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-search-result',
  templateUrl: './search-result.component.html',
  styleUrls: ['./search-result.component.css']
})
export class SearchResultComponent implements OnInit, AfterViewInit {

  results = [];
  resultFields = [];
  dataTable: any;
  searchQuery: QueryBuilder;
  showQuery = false;
  searchType: string;
  error: any;
  loading = false;
  staticResults = false;
  previousUrl = ['../advanced'];
  temp = [];
  searchHandler = new Subject();
  @ViewChild(DatatableComponent) table: DatatableComponent;
  @ViewChild('parent') parent: ElementRef;
  columnMode = ColumnMode;
  tableWidth: number;
  cellWidth: number;B

  constructor(
    private queryBuilder: QueryBuilderService,
    private chRef: ChangeDetectorRef,
    private router: Router,
    private route: ActivatedRoute,
    private spinner: NgxSpinnerService
  ) { }

  ngOnInit() {
    this.loading = true;
    this.searchType = this.queryBuilder.getSearchType();
    this.searchQuery = this.queryBuilder.getCurrentObject();
    this.spinner.show();
    
    this.route.queryParams.subscribe(queryParam => {
      if (queryParam['redirect'] === 'home') {
        this.previousUrl = ['/home']
      }

      if (queryParam['category'] === 'SDT_') {
        this.staticResults = true;
      }
    });

    this.searchHandler.pipe(
      debounceTime(500)
    ).subscribe(event => this.handleSearch(event));
  }

  ngAfterViewInit() {
    this.queryBuilder.getSearchResults()
      .subscribe((res: any) => {
        this.loading = false;
        this.spinner.hide();
        this.results = [...res.data];
        this.temp = res.data;
        this.resultFields = [...res.schema.fields
        .map((field) => ({
          prop: field.name,
          name: field.name,
          width: this.tableWidth / res.schema.fields.length + 1
        }))];
        this.chRef.detectChanges();
      }
    );
  }

  updateFilter(event) {
    this.searchHandler.next(event);
  }
  
  handleSearch(event) {
    const val = event.target.value.toLowerCase();
    const temp = this.temp.filter(row => {
      const fields = Object.keys(row);
      for (const field of fields) {
        if (row[field] && row[field].toString().toLowerCase().includes(val)) {
          return true;
        }
      }
      return false;
    });

    this.results = temp;
    this.table.offset = 0;
  }

  isLink(td: string) {
    return /https?:\/\/.*/.test(td);
  }

  isImage(td: string, field: string) {
    return field === 'link' && /\.(gif|jpe?g|tiff?|png|webp|)$/i.test(td);
  }

  getImgSrc(url: string) {
    // return `${environment.baseURL}${url}`;
    return 'https://picsum.photos/200/200'
  }

  viewData(id) {
    this.router.navigate([`search/result/brick/${id}`]);
  }

  viewCoreData(id) {
    this.router.navigate([`search/result/core/${id}`]);
  }

  useData(id) {
    this.queryBuilder.setPreviousUrl('/search/result');
    this.router.navigate([`../../plot/options/${id}`], {relativeTo: this.route});
  }

  handleCoreTypeDownload() {
    if (this.results) {
      const replacer = (key, value) => value === null ? '' : value;
      const tsv = this.results.map(row => {
        return this.resultFields
          .map(field => JSON.stringify(row[field.name], replacer))
          .join('\t');
      });
      tsv.unshift(this.resultFields.map(field => field.name).join('\t'));
      const tsvArray = tsv.join('\n');

      const a = document.createElement('a');
      const blob = new Blob([tsvArray], { type: 'text/tsv' });
      const url = window.URL.createObjectURL(blob);

      a.href = url;
      a.download = `download-${new Date().toISOString()}.tsv`;
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    }

  }

}
