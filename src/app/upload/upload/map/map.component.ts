import { Component, OnInit, OnDestroy, TemplateRef } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, DimensionVariable, TypedProperty, Term, DataValue } from 'src/app/shared/models/brick';
import { NgxSpinnerService } from 'ngx-spinner';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { ValidationErrorItemComponent } from './validation-error-item/validation-error-item.component';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements OnInit, OnDestroy {

  brick: Brick;
  dimVars: DimensionVariable[] = [];
  properties: TypedProperty[];
  dataVars: DataValue[];
  testArray = [];
  mapped = false;
  loading = false;
  error = false;
  errorSub: Subscription;
  modalRef: BsModalRef;


  constructor(
    private uploadService: UploadService,
    private spinner: NgxSpinnerService,
    private validator: UploadValidationService,
    private modalService: BsModalService
    ) { }

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.dataVars = this.brick.dataValues;
    this.properties = this.brick.properties;

    let dimCount = 0;
    this.brick.dimensions.forEach(dim => {
      dimCount += dim.variables.length;
      this.dimVars = [...this.dimVars, ...dim.variables];
    });

    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => this.error = error);
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }


  getValidationResults() {
    this.dimVars.forEach((_, i) => { this.spinner.show('d' + i); });
    this.dataVars.forEach((_, i) => { this.spinner.show('v' + i); });

    this.uploadService.getValidationResults()
      .subscribe((data: any) => {
        this.dimVars.forEach((_, i) => { this.spinner.hide('d' + i); });
        this.dataVars.forEach((_, i) => { this.spinner.hide('v' + i); });
        const { data_vars, dims } = data.results;

        // assign counts to data vars
        data_vars.forEach((dv, i) => {
          const brickDv: DataValue = this.brick.dataValues[i];
          brickDv.validCount = dv.valid_count;
          brickDv.invalidCount = dv.invalid_count;
          brickDv.totalCount = dv.total_count;
        });

        // assign counts to dim vars
        dims.forEach((dim, i) => {
          const brickDim: BrickDimension = this.brick.dimensions[i];
          dim.dim_vars.forEach((dv, j) => {
            const brickDimVar = brickDim.variables[j];
            brickDimVar.validCount = dv.valid_count;
            brickDimVar.invalidCount = dv.invalid_count;
            brickDimVar.totalCount = dv.total_count;
          });
        });

        this.mapped = true;
      });
  }
  
  getMappedStatus(valid, total) {
    if (valid === total) {
      return 'status-column-success';
    }
    return valid === 0 ? 'status-column-fail' : 'status-column-warn';
  }

  getPropValueDisplay(prop: TypedProperty) {
    return prop.scalarType === 'oterm_ref'
      ? (prop.value as Term).text
      : prop.value;
  }

  openModal(index: number, dimVarIndex?: string) {
    const config: any = { class: 'modal-lg' };
    if (typeof dimVarIndex === 'number') {
      // open modal ref for dimension variables
      this.uploadService.getDimVarValidationErrors(index, dimVarIndex)
        .subscribe((res: any) => {
          config.initialState = { errors: res.results };
          this.modalRef = this.modalService.show(ValidationErrorItemComponent, config);
        });
    } else {
      // open modal ref for data variables
      this.uploadService.getDataVarValidationErrors(index)
        .subscribe((res: any) => {
          config.initialState = { errors: res.results };
          this.modalRef = this.modalService.show(ValidationErrorItemComponent, config);
        });
    }
  }

}
