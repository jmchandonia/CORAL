import { Component, OnInit, ChangeDetectorRef, TemplateRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { UploadService } from 'src/app/shared/services/upload.service';
import { NgxSpinnerService } from 'ngx-spinner';
import { ColumnMode } from '@swimlane/ngx-datatable';
import {BsModalRef, BsModalService} from 'ngx-bootstrap/modal';
import { Response } from 'src/app/shared/models/response';
@Component({
  selector: 'app-core-type-result',
  templateUrl: './core-type-result.component.html',
  styleUrls: ['./core-type-result.component.css']
})
export class CoreTypeResultComponent implements OnInit {

  constructor(
    private route: ActivatedRoute,
    private uploadService: UploadService,
    private spinner: NgxSpinnerService,
    private chRef: ChangeDetectorRef,
    private modalService: BsModalService
  ) { }

  public updatingDuplicates = false;
  public duplicateResults: any;
  public duplicateUpdateErrors: number;
  public propertyUnits: any; // for displaying units of fields in UI


  private batchId: string;
  columnMode = ColumnMode;

  private modalRef: BsModalRef;

  // TODO: figure out a way to have less variables for this

  public errorResults: any[];
  public errorResultFields: any[];

  public successResults: any[];
  public successResultFields: any[] = [];

  public warningResults: any[];
  public warningResultFields: any[];

  public processErrorResults: any[];
  public processErrorResultFields: any[];

  public processWarningResults: any[];
  public processWarningResultFields: any[];

  ngOnInit(): void {
    this.spinner.show('spinner')
    this.route.params.subscribe(params => {
      this.batchId = params['batchId'];
      this.uploadService.getCoreTypeUploadResults(this.batchId)
        .subscribe(({results}) => {
          this.errorResults = results['errors'];
          if (this.errorResults.length) {
            this.errorResultFields = Object.keys(results['errors'][0]['data']).map(d => ({prop: d, name: d}));
          }

          this.successResults = results['success'];
          if (this.successResults.length) {
            this.successResultFields = Object.keys(results['success'][0]).map(d => ({prop: d, name: d}))
          }

          this.warningResults = results['warnings'];
          if (this.warningResults.length) {
            this.warningResultFields = Object.keys(results['warnings'][0]['old_data']).map(d => ({prop: d, name: d}))
          }

          this.processErrorResults = results['process_errors'];
          if (this.processErrorResults.length) {
            this.processErrorResultFields = Object.keys(results['process_errors'][0]['data']).map(d => ({prop: d, name: d}));
          }

          this.processWarningResults = results['process_warnings'];
          if (this.processWarningResults.length) {
            this.processWarningResultFields = Object.keys(results['process_warnings'][0]['old_data'])
              .map(d => ({prop: d, name: d}))
              .filter(d => !d.name.startsWith('_') && !d.name.includes('_objects'))
          }

          this.propertyUnits = results['property_units'];
          this.spinner.hide('spinner');
          this.chRef.detectChanges();
        });
    });
  }

  // Open confirmation window before updating templates
  displayModal(template: TemplateRef<any>) {
    this.modalRef = this.modalService.show(template, {class: 'modal-lg'});
  }

  cancel() {
    this.modalRef.hide();
  }

  updateAllDuplicates() {
    this.modalRef.hide();

    this.modalService.onHidden.subscribe(() => {
      this.updatingDuplicates = true;
      this.spinner.show('updatingDuplicates');
      this.uploadService.updateCoreTypeDuplicates(this.batchId)
        .subscribe((data: Response<any>) => {
          this.duplicateResults = data.results;
          this.updatingDuplicates = false;
          this.spinner.hide('updatingDuplicates');

          // get number of successful uploads for UI
          this.duplicateUpdateErrors = this.duplicateResults.reduce((a, c) => c.error ? a + 1 : a, 0)
        })
    })


  }

}
