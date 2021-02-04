import { async, ComponentFixture, TestBed, tick, fakeAsync, flushMicrotasks, flush } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { LoadComponent } from './load.component';
import { MockComponent } from 'ng-mocks';
import { LoadSuccessTableComponent } from './load-success-table/load-success-table.component';
import { UploadService } from 'src/app/shared/services/upload.service';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subject } from 'rxjs';

describe('LoadComponent', () => {

  const MockUploadService = {
    downloadBrickTemplate: () => Promise.resolve(new Blob()),
    setFile: (file) => {},
    uploadBrick: (file: File) => Promise.resolve({
      results: {testData: 'test'}
    })
  }

  const errorSub = new Subject();

  const MockValidator = {
    getValidationErrors: () => errorSub
  }

  let spectator: Spectator<LoadComponent>;
  const createComponent = createComponentFactory({
    component: LoadComponent,
    imports: [
      NgxSpinnerModule,
      HttpClientModule
    ],
    providers: [
      mockProvider(UploadService, MockUploadService),
      mockProvider(UploadValidationService, MockValidator)
    ],
    entryComponents: [
      MockComponent(LoadSuccessTableComponent)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should initialize component to get brick and data', () => {
    spyOn(spectator.component, 'getUploadData');
    spectator.component.ngOnInit();
    expect(spectator.component.getUploadData).toHaveBeenCalled();
  });

  it('should trigger template download on click', () => {
    jasmine.getEnv().allowRespy(true)
    spectator.detectChanges();
    const uploadService = spectator.get(UploadService);
    spyOn(spectator.component, 'downloadTemplate').and.callThrough();
    spyOn(uploadService, 'downloadBrickTemplate');
    spectator.click('button#download-template');
    spectator.detectChanges();

    expect(spectator.component.downloadTemplate).toHaveBeenCalled();
    expect(uploadService.downloadBrickTemplate).toHaveBeenCalled();
  });

  it('should download brick template', fakeAsync(() => {
    const uploadService = spectator.get(UploadService);
    spyOn(uploadService, 'downloadBrickTemplate').and.callThrough();
    spyOn(spectator.component, 'addUrlToPageAndClick');
    spectator.detectChanges();
    spectator.component.downloadTemplate();
    flushMicrotasks();
    expect(spectator.component.addUrlToPageAndClick).toHaveBeenCalled();    
  }));

  it('should handle upload on drag', () => {
    const uploadService = spectator.get(UploadService);
    spyOn(uploadService, 'setFile');
    spyOn(spectator.component, 'handleFileInput').and.callThrough();
    spyOn(spectator.component, 'calculateFileSize');

    const file = new File([''], 'test-file.xlsx');
    spectator.triggerEventHandler('div.drop-zone', 'fileDropped', {
        item: (n: number) => file,
        length: 1
    } as FileList);
    spectator.detectChanges();
    expect(spectator.component.handleFileInput).toHaveBeenCalled();
    expect(spectator.component.calculateFileSize).toHaveBeenCalled();
    expect(spectator.component.file).toEqual(file);
    expect(uploadService.setFile).toHaveBeenCalled();
  });

  it('should handle file input from browse window', () => {
    const uploadService = spectator.get(UploadService);
    spyOn(uploadService, 'setFile');
    spyOn(spectator.component, 'handleFileInputFromBrowse').and.callThrough();
    spyOn(spectator.component, 'calculateFileSize');

    const file = new File([''], 'test-file-from-browse.xlsx');
    spectator.triggerEventHandler('input#file', 'change', {
      preventDefault: () => {},
      target: {
        files: {
          item: n => file
        }
      }
    });
    spectator.detectChanges();
    expect(spectator.component.handleFileInputFromBrowse).toHaveBeenCalled();
    expect(spectator.component.calculateFileSize).toHaveBeenCalled();
    expect(spectator.component.file).toEqual(file);
    expect(uploadService.setFile).toHaveBeenCalled();
  });

  it('should upload file to service', fakeAsync(() => {
    spectator.detectChanges();
    const uploadService = spectator.get(UploadService);
    spyOn(spectator.component, 'upload').and.callThrough();
    spyOn(uploadService, 'uploadBrick').and.callThrough();
    spyOn(uploadService, 'setSuccessData');

    spectator.component.file = new File([''], 'test-upload.xlsx');
    spectator.detectChanges();
    spectator.click('button#upload-brick');
    spectator.detectChanges();
    expect(spectator.component.upload).toHaveBeenCalled();
    expect(uploadService.uploadBrick).toHaveBeenCalled();
    flushMicrotasks();
    tick();
    spectator.detectChanges();
    expect(uploadService.setSuccessData).toHaveBeenCalledWith({testData: 'test'});
    expect(spectator.component.successData).toEqual({testData: 'test'});
    expect(spectator.query('app-load-success-table')).not.toBeNull();
  }));

  it('should remove file', () => {
    const uploadService = spectator.get(UploadService);
    spyOn(spectator.component, 'removeFile').and.callThrough();
    spyOn(uploadService, 'setSuccessData');
    spyOn(uploadService, 'setFile');
    spectator.component.file = new File([''], 'test-remove.xlsx');
    spectator.detectChanges();

    spectator.click('button#remove-file');
    spectator.detectChanges();
    expect(spectator.component.removeFile).toHaveBeenCalled();
    expect(uploadService.setSuccessData).toHaveBeenCalledWith(null);
    expect(uploadService.setFile).toHaveBeenCalledWith(null);
    expect(spectator.component.successData).toBeUndefined();
  });

  it('should subscribe to validation errors', () => {
    errorSub.next(true);
    spectator.detectChanges();
    expect(spectator.component.validationError).toBeTruthy();
    expect(spectator.query('div.alert.alert-danger')).not.toBeNull();
  });

});
