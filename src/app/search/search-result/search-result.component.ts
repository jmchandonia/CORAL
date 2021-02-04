import { Component, OnInit, ChangeDetectorRef, AfterViewInit, ViewChild, ChangeDetectionStrategy, SecurityContext } from '@angular/core';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder } from '../../shared/models/QueryBuilder';
import { Router, ActivatedRoute } from '@angular/router';
import { NgxSpinnerService } from 'ngx-spinner';
import { DatatableComponent } from '@swimlane/ngx-datatable';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { ColumnMode } from '@swimlane/ngx-datatable';
import { DomSanitizer } from '@angular/platform-browser'
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { ImageDisplayComponent } from './image-display/image-display.component';

@Component({
  selector: 'app-search-result',
  templateUrl: './search-result.component.html',
  styleUrls: ['./search-result.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
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
  columnMode = ColumnMode;
  tableWidth: number;
  modalRef: BsModalRef;

  constructor(
    private queryBuilder: QueryBuilderService,
    private chRef: ChangeDetectorRef,
    private router: Router,
    private route: ActivatedRoute,
    private spinner: NgxSpinnerService,
    private modalService: BsModalService,
    private sanitizer: DomSanitizer
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
        if (this.temp.length) { this.getImageUrls(); }
      }
    );
  }

  getImageUrls() {
    this.table?.bodyComponent.temp.forEach(async (row) => {
      if (row.link && this.isImage(row.link, 'link') && !row._imgSrc) {
        row._imgSrc = await this.queryBuilder.getImageSrc(row.link.substring(1));
        this.chRef.detectChanges();
      }
    });
  }

  displayImage(imgSrc, name) {
    const initialState = {
      title: name,
      imgSrc
    }
    this.modalRef = this.modalService.show(ImageDisplayComponent, {initialState, class: 'modal-lg'})
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

  handlePaging(event) {
    this.chRef.detectChanges();
    this.getImageUrls();
  }

  viewData(id) {
    const queryParams = this.previousUrl[0] === '/home' ? { redirect: 'home' } : {};
    this.router.navigate([`search/result/brick/${id}`], {queryParams});
  }

  viewCoreData(id) {
    const queryParams = this.previousUrl[0] === '/home' ? { redirect: 'home' } : {};
    this.router.navigate([`search/result/core/${id}`], {queryParams});
  }

  plotDynamicTypeResults(id) {
    this.queryBuilder.setPreviousUrl('/search/result');
    this.router.navigate([`../../plot/options/${id}`], {relativeTo: this.route});
  }

  plotCoreTypeResults() {
    const queryBuilder = localStorage.getItem('queryBuilder');
    localStorage.setItem('coreTypePlotParams', queryBuilder);
    this.router.navigate(['plot/options'], {
      queryParams: {
        coreType: JSON.parse(queryBuilder).queryMatch.dataType
      }
    })
  }

  // download all core type search results as tsv
  handleCoreTypeDownload() {
    this.queryBuilder.getSearchResults('TSV')
      .subscribe(data => {
        const filename = JSON.parse(localStorage.getItem('queryBuilder'))?.queryMatch?.dataType || 'core-type';
        this.download(data, filename + new Date().toISOString())
      });
  }

  handleDownload(row) {
    // download actual image
      if (row._imgSrc) {
        const a = document.createElement('a');
        a.href = this.sanitizer.sanitize(SecurityContext.URL, row._imgSrc);
        a.download = row.name;
        a.setAttribute('display', 'none');
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        if (row.brick_id) {
          // download dynamic type tsv
          this.queryBuilder.downloadBrick(row.brick_id, 'TSV')
            .subscribe(data => {
              this.download(data.res, row.brick_name);
            });
        } else {
          // download singular core type tsv
          this.queryBuilder.downloadCoreType(row.id)
            .subscribe(data => {
              this.download(data.results.items, row.name);
          });
        }
      }
  }

  download(data, name) {
    const blob = new Blob([data], {type: 'text/tsv'});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name}.tsv`;
    a.setAttribute('display', 'none');
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

}
