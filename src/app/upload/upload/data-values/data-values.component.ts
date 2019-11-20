import { Component, OnInit, OnDestroy } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, DataValue } from 'src/app/shared/models/brick';
import { Subscription } from 'rxjs';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

@Component({
  selector: 'app-data-values',
  templateUrl: './data-values.component.html',
  styleUrls: ['./data-values.component.css']
})
export class DataValuesComponent implements OnInit, OnDestroy {

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService
    ) { }

  dataValues: DataValue[];
  brick: Brick;
  error = false;
  errorSub: Subscription;

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.dataValues = this.brick.dataValues;
    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => this.error = error);
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  addDataValue() {
    this.dataValues.push(new DataValue(this.dataValues.length, false));
  }

  removeDataValue(index) {
    this.dataValues.splice(index, 1);
    this.brick.resetDataValueIndices();
  }

  resetDataValue(event: DataValue, index: number) {
    this.dataValues.splice(index, 1, event);
  }

}
